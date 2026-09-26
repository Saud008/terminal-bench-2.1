package engine

import (
	"fmt"

	"brickmake/internal/diag"
)

// outdated reports whether prerequisite d makes target n out of date. A
// prerequisite that is phony, missing, or remade in a dry run always does.
func (e *Engine) outdated(d, n *node) bool {
	if d.f.Phony || d.st.newest || !d.st.exists {
		return true
	}
	return !n.st.exists || d.st.t.After(n.st.t)
}

func (e *Engine) noRule(n, parent *node) {
	msg := fmt.Sprintf("No rule to make target '%s'", n.name())
	if parent != nil {
		msg += fmt.Sprintf(", needed by '%s'", parent.name())
	}
	if e.KeepGoing {
		diag.Err("*** %s.", msg)
	} else {
		diag.Err("*** %s.  Stop.", msg)
	}
}

func (e *Engine) fail(n, parent *node, depFailure bool) status {
	n.state, n.status = done, failed
	if depFailure && parent == nil && e.KeepGoing && !e.DryRun {
		diag.Err("Target '%s' not remade because of errors.", n.name())
	}
	return failed
}

// update brings n up to date on behalf of parent (nil for a goal).
func (e *Engine) update(n, parent *node) status {
	switch n.state {
	case done:
		return n.status
	case running:
		diag.Err("Circular %s <- %s dependency dropped.", parent.name(), n.name())
		return dropped
	}
	n.state = running
	if n.parent == nil {
		n.parent = parent
	}
	e.implicitFor(n)
	deps := e.depsOf(n)
	n.stat()
	if !n.hasRule() && !n.st.exists {
		e.noRule(n, parent)
		return e.fail(n, parent, false)
	}

	must, bad := false, false
	for _, d := range deps {
		var st status
		if d.n.intermediate && d.n.state != done {
			hit := false
			st = e.checkIntermediate(d.n, n, &hit)
			if hit && !d.order {
				must = true
			}
		} else {
			st = e.update(d.n, n)
			if st == ok && !d.order && e.outdated(d.n, n) {
				must = true
			}
		}
		if st == failed {
			bad = true
			if !e.KeepGoing {
				break
			}
		}
	}
	if bad {
		return e.fail(n, parent, true)
	}
	if n.f.Phony || !n.st.exists || e.AlwaysMake {
		must = true
	}
	if !must {
		n.state, n.status = done, ok
		return ok
	}
	for _, d := range deps {
		if d.n.intermediate && d.n.state != done {
			if e.update(d.n, n) == failed {
				bad = true
				if !e.KeepGoing {
					break
				}
			}
		}
	}
	if bad {
		return e.fail(n, parent, true)
	}
	return e.remake(n)
}

// checkIntermediate decides whether a missing intermediate file matters to
// target: it does when the intermediate exists and is newer than target,
// or when anything it depends on is. The intermediate itself is only made
// later, if target has to be remade.
func (e *Engine) checkIntermediate(m, target *node, hit *bool) status {
	if m.parent == nil {
		m.parent = target
	}
	e.implicitFor(m)
	m.stat()
	if m.st.exists && (!target.st.exists || m.st.t.After(target.st.t)) {
		*hit = true
		return ok
	}
	if !m.hasRule() {
		return ok
	}
	for _, d := range e.depsOf(m) {
		var st status
		if d.n.intermediate && d.n.state != done {
			sub := false
			st = e.checkIntermediate(d.n, target, &sub)
			if sub && !d.order {
				*hit = true
			}
		} else {
			st = e.update(d.n, m)
			if st == ok && !d.order && e.outdated(d.n, target) {
				*hit = true
			}
		}
		if st == failed && !e.KeepGoing {
			return failed
		}
	}
	return ok
}

// remake runs n's recipe, or records that a target without a recipe was
// "remade" by doing nothing.
func (e *Engine) remake(n *node) status {
	if n.recipe == nil {
		n.state, n.status = done, ok
		n.stat()
		return ok
	}
	auto := e.autoVars(n)
	n.started = true
	good := e.run(n, auto)
	n.state = done
	if !good {
		n.status = failed
		return failed
	}
	n.status = ok
	e.refresh(n)
	if n.match != nil {
		for _, name := range n.match.also {
			o := e.node(e.db.Enter(name))
			if o.state != done {
				o.state, o.status, o.started = done, ok, true
				o.intermediate = o.intermediate || n.intermediate
				e.refresh(o)
			}
		}
	}
	return ok
}

// refresh records that a remade target is now newer than everything
// considered before it.
func (e *Engine) refresh(n *node) {
	if e.DryRun && allForced(n.recipe) {
		n.stat()
		return
	}
	n.st = stamp{exists: true, newest: true}
}

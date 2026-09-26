// Package engine decides which targets are out of date and runs their
// recipes.
package engine

import (
	"fmt"
	"os"

	"brickmake/internal/db"
	"brickmake/internal/diag"
	"brickmake/internal/expand"
)

// Engine updates goals against a rule database.
type Engine struct {
	DryRun     bool
	Silent     bool
	KeepGoing  bool
	AlwaysMake bool
	Shell      string
	Env        []string

	db      *db.DB
	x       *expand.Expander
	nodes   map[*db.File]*node
	order   []*node
	started int
}

func New(d *db.DB, x *expand.Expander) *Engine {
	return &Engine{db: d, x: x, nodes: map[*db.File]*node{}, Shell: "/bin/sh"}
}

func (e *Engine) node(f *db.File) *node {
	if n := e.nodes[f]; n != nil {
		return n
	}
	n := &node{f: f}
	e.nodes[f] = n
	e.order = append(e.order, n)
	return n
}

// Run updates the goals in order and returns the exit status.
func (e *Engine) Run(goals []string) (code int) {
	defer e.removeIntermediates()
	defer func() {
		if r := recover(); r != nil {
			f, isFatal := r.(diag.Fatal)
			if !isFatal {
				panic(r)
			}
			fmt.Fprintln(diag.Stderr, f.Error())
			code = 2
		}
	}()
	anyFailed := false
	for _, g := range goals {
		n := e.node(e.db.Enter(g))
		if e.update(n, nil) == failed {
			anyFailed = true
			if !e.KeepGoing {
				break
			}
			continue
		}
		if e.started == 0 {
			if n.f.Phony || n.recipe == nil {
				diag.Say("Nothing to be done for '%s'.", g)
			} else {
				diag.Say("'%s' is up to date.", g)
			}
		}
	}
	if anyFailed {
		return 2
	}
	return 0
}

// removeIntermediates deletes the intermediate files made by this run.
func (e *Engine) removeIntermediates() {
	first := true
	for _, n := range e.order {
		if !n.intermediate || !n.started || n.f.Precious || e.db.SecondaryAll {
			continue
		}
		if !e.DryRun {
			if err := os.Remove(n.name()); err != nil && os.IsNotExist(err) {
				continue
			}
		}
		if e.Silent {
			continue
		}
		if first {
			fmt.Fprint(diag.Stdout, "rm ")
			first = false
		} else {
			fmt.Fprint(diag.Stdout, " ")
		}
		fmt.Fprint(diag.Stdout, n.name())
	}
	if !first {
		fmt.Fprintln(diag.Stdout)
	}
}

package engine

import (
	"errors"
	"fmt"
	"os"
	"os/exec"

	"brickmake/internal/db"
	"brickmake/internal/diag"
	"brickmake/internal/expand"
)

type command struct {
	text                  string
	silent, ignore, force bool
	pos                   diag.Pos
}

// prefixes strips leading blanks and '@', '-', '+' prefixes into c.
func prefixes(s string, c *command) string {
	for len(s) > 0 {
		switch s[0] {
		case '@':
			c.silent = true
		case '-':
			c.ignore = true
		case '+':
			c.force = true
		case ' ', '\t':
		default:
			return s
		}
		s = s[1:]
	}
	return s
}

func allForced(r *db.Recipe) bool {
	if r == nil || len(r.Lines) == 0 {
		return false
	}
	for _, l := range r.Lines {
		var c command
		prefixes(l, &c)
		if !c.force {
			return false
		}
	}
	return true
}

// run expands every line of n's recipe, then executes the lines in order.
func (e *Engine) run(n *node, auto *expand.Auto) bool {
	sc := e.scope(n)
	sc.Auto = auto
	var cmds []command
	for i, raw := range n.recipe.Lines {
		c := command{pos: n.recipe.Pos[i]}
		raw = prefixes(raw, &c)
		e.x.Pos = c.pos
		c.text = prefixes(e.x.Expand(raw, sc), &c)
		cmds = append(cmds, c)
	}
	for _, c := range cmds {
		if c.text == "" {
			continue
		}
		e.started++
		if e.DryRun || (!c.silent && !e.Silent) {
			fmt.Fprintln(diag.Stdout, c.text)
		}
		if e.DryRun && !c.force {
			continue
		}
		code := e.exec(c.text)
		if code == 0 {
			continue
		}
		if c.ignore {
			diag.Err("[%s: %s] Error %d (ignored)", c.pos, n.name(), code)
			continue
		}
		diag.Err("*** [%s: %s] Error %d", c.pos, n.name(), code)
		return false
	}
	return true
}

func (e *Engine) exec(line string) int {
	cmd := exec.Command(e.Shell, "-c", line)
	cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, os.Stdout, os.Stderr
	cmd.Env = e.Env
	err := cmd.Run()
	if err == nil {
		return 0
	}
	var ee *exec.ExitError
	if errors.As(err, &ee) {
		if code := ee.ExitCode(); code > 0 {
			return code
		}
		return 1
	}
	return 127
}

// ShellOutput runs a $(shell ...) command and returns its standard output.
func (e *Engine) ShellOutput(line string) string {
	cmd := exec.Command(e.Shell, "-c", line)
	cmd.Stdin, cmd.Stderr = os.Stdin, os.Stderr
	cmd.Env = e.Env
	out, _ := cmd.Output()
	return string(out)
}

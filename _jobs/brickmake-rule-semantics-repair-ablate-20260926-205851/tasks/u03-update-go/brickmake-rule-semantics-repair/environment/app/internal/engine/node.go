package engine

import (
	"os"
	"time"

	"brickmake/internal/db"
	"brickmake/internal/vars"
)

type state int

const (
	fresh state = iota
	running
	done
)

type status int

const (
	ok status = iota
	failed
	dropped // circular dependency, ignored by the parent
)

// stamp is a file's modification time as seen by the engine. Newest
// marks a target that counts as just remade without a new time on disk
// (dry runs).
type stamp struct {
	exists bool
	t      time.Time
	newest bool
}

func statFile(name string) stamp {
	fi, err := os.Stat(name)
	if err != nil {
		return stamp{}
	}
	return stamp{exists: true, t: fi.ModTime()}
}

// node is the run-time state of one file.
type node struct {
	f      *db.File
	state  state
	status status
	st     stamp
	parent *node

	searched     bool
	match        *match
	preset       *match // chosen for an intermediate by the parent's search
	intermediate bool
	recipe       *db.Recipe
	stem         string

	depsReady bool
	deps      []dep

	patReady bool
	patVars  *vars.Set

	started bool // its recipe was started
}

type dep struct {
	n     *node
	order bool
}

func (n *node) name() string { return n.f.Name }

func (n *node) stat() { n.st = statFile(n.f.Name) }

// hasRule reports whether make knows how to (re)make the file, even if the
// answer is "do nothing".
func (n *node) hasRule() bool {
	return len(n.f.Rules) > 0 || n.match != nil || n.f.Phony
}

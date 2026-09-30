// Package vars stores makefile variables.
package vars

import (
	"sort"

	"brickmake/internal/diag"
)

type Flavor int

const (
	Recursive Flavor = iota
	Simple
)

func (f Flavor) String() string {
	if f == Simple {
		return "simple"
	}
	return "recursive"
}

type Origin int

const (
	Undefined Origin = iota
	Default
	Environment
	File
	CommandLine
	Automatic
)

func (o Origin) String() string {
	switch o {
	case Default:
		return "default"
	case Environment:
		return "environment"
	case File:
		return "file"
	case CommandLine:
		return "command line"
	case Automatic:
		return "automatic"
	}
	return "undefined"
}

// Var is one variable definition. Append marks a target- or
// pattern-specific "+=" whose value is added to the value visible from
// the enclosing scope at expansion time.
type Var struct {
	Name   string
	Value  string
	Flavor Flavor
	Origin Origin
	Append bool
	Pos    diag.Pos
}

// Set is one level of variable definitions.
type Set struct {
	m map[string]*Var
}

func NewSet() *Set { return &Set{m: map[string]*Var{}} }

func (s *Set) Get(name string) *Var {
	if s == nil {
		return nil
	}
	return s.m[name]
}

func (s *Set) Put(v *Var) { s.m[v.Name] = v }

func (s *Set) Len() int {
	if s == nil {
		return 0
	}
	return len(s.m)
}

func (s *Set) Names() []string {
	names := make([]string, 0, len(s.m))
	for n := range s.m {
		names = append(names, n)
	}
	sort.Strings(names)
	return names
}

// Op is an assignment operator.
type Op int

const (
	OpRecursive   Op = iota // =
	OpSimple                // := and ::=
	OpAppend                // +=
	OpConditional           // ?=
)

func (o Op) String() string {
	switch o {
	case OpSimple:
		return ":="
	case OpAppend:
		return "+="
	case OpConditional:
		return "?="
	}
	return "="
}

// Paste joins an old value and an appended value. An empty appended value
// leaves the old value unchanged.
func Paste(old, add string) string {
	if add == "" {
		return old
	}
	if old == "" {
		return add
	}
	return old + " " + add
}

package resolve

import (
	"fmt"
	"sort"
	"strings"
)

// UnsatisfiableError means no eligible release meets a package's constraints.
type UnsatisfiableError struct {
	Package     string
	Constraints []Constraint
}

func (e *UnsatisfiableError) Error() string {
	parts := make([]string, len(e.Constraints))
	for i, c := range e.Constraints {
		parts[i] = fmt.Sprintf("%q (from %s)", c.Raw, c.From)
	}
	return fmt.Sprintf("no version of %s satisfies %s", e.Package, strings.Join(parts, ", "))
}

// UnknownPackageError means a required package is missing from the registry.
type UnknownPackageError struct {
	Package    string
	RequiredBy []string
}

func (e *UnknownPackageError) Error() string {
	return fmt.Sprintf("unknown package %q (required by %s)", e.Package, strings.Join(e.RequiredBy, ", "))
}

func dependents(cons []Constraint) []string {
	seen := map[string]bool{}
	var out []string
	for _, c := range cons {
		if !seen[c.From] {
			seen[c.From] = true
			out = append(out, c.From)
		}
	}
	sort.Strings(out)
	return out
}

// Package cli implements the pinwheel command line.
package cli

import (
	"fmt"
	"io"
)

const (
	exitOK      = 0
	exitUsage   = 2
	exitResolve = 3
)

type command struct {
	name     string
	synopsis string
	run      func(args []string, stdout, stderr io.Writer) int
}

var commands = []command{
	{"satisfies", "satisfies VERSION RANGE", runSatisfies},
	{"compare", "compare VERSION VERSION", runCompare},
	{"resolve", "resolve [--registry DIR] PROJECT_DIR", runResolve},
}

// Run executes one pinwheel invocation and returns the process exit status.
func Run(args []string, stdout, stderr io.Writer) int {
	if len(args) == 0 {
		usage(stderr)
		return exitUsage
	}
	switch args[0] {
	case "help", "-h", "--help":
		usage(stdout)
		return exitOK
	}
	for _, c := range commands {
		if c.name == args[0] {
			return c.run(args[1:], stdout, stderr)
		}
	}
	fmt.Fprintf(stderr, "pinwheel: unknown command %q\n", args[0])
	usage(stderr)
	return exitUsage
}

func usage(w io.Writer) {
	fmt.Fprintln(w, "usage:")
	for _, c := range commands {
		fmt.Fprintf(w, "  pinwheel %s\n", c.synopsis)
	}
}

func fail(stderr io.Writer, code int, format string, a ...any) int {
	fmt.Fprintf(stderr, "pinwheel: "+format+"\n", a...)
	return code
}

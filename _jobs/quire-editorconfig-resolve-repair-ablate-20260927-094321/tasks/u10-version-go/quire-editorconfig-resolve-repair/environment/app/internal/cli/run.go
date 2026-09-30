// Package cli implements the quire command line.
package cli

import (
	"bufio"
	"fmt"
	"io"

	"quire/internal/resolve"
)

// Main runs quire and returns its exit status.
func Main(argv []string, stdin io.Reader, stdout, stderr io.Writer) int {
	out := bufio.NewWriter(stdout)
	defer out.Flush()

	opts, code, done := parseArgs(argv, out, stderr)
	if done {
		return code
	}
	ro := resolve.Options{ConfName: opts.confName, Version: opts.version.Effective()}
	headers := len(opts.paths) > 1
	in := newInputs(opts.paths, stdin)
	for {
		f, ok := in.next()
		if !ok {
			return 0
		}
		if headers {
			fmt.Fprintf(out, "[%s]\n", f.name)
		}
		pairs, err := resolve.File(f.name, ro)
		if err != nil {
			out.Flush()
			fmt.Fprintln(stderr, err)
			return 1
		}
		for _, p := range pairs {
			fmt.Fprintf(out, "%s=%s\n", p.Name, p.Value)
		}
	}
}

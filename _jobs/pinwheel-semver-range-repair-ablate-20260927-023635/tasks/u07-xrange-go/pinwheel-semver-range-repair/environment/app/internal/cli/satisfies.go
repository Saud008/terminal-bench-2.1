package cli

import (
	"fmt"
	"io"

	"github.com/brightloom/pinwheel/internal/semrange"
	"github.com/brightloom/pinwheel/internal/semver"
)

func runSatisfies(args []string, stdout, stderr io.Writer) int {
	if len(args) != 2 {
		return fail(stderr, exitUsage, "satisfies takes a version and a range")
	}
	v, err := semver.Parse(args[0])
	if err != nil {
		return fail(stderr, exitUsage, "%v", err)
	}
	r, err := semrange.Parse(args[1])
	if err != nil {
		return fail(stderr, exitUsage, "%v", err)
	}
	fmt.Fprintln(stdout, r.Test(v))
	return exitOK
}

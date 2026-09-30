package cli

import (
	"fmt"
	"io"

	"github.com/brightloom/pinwheel/internal/semver"
)

func runCompare(args []string, stdout, stderr io.Writer) int {
	if len(args) != 2 {
		return fail(stderr, exitUsage, "compare takes two versions")
	}
	a, err := semver.Parse(args[0])
	if err != nil {
		return fail(stderr, exitUsage, "%v", err)
	}
	b, err := semver.Parse(args[1])
	if err != nil {
		return fail(stderr, exitUsage, "%v", err)
	}
	fmt.Fprintln(stdout, semver.Compare(a, b))
	return exitOK
}

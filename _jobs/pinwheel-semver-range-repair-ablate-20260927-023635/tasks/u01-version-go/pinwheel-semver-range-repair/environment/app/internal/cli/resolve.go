package cli

import (
	"flag"
	"fmt"
	"io"
	"path/filepath"

	"github.com/brightloom/pinwheel/internal/lockfile"
	"github.com/brightloom/pinwheel/internal/manifest"
	"github.com/brightloom/pinwheel/internal/registry"
	"github.com/brightloom/pinwheel/internal/resolve"
)

const defaultRegistry = "/app/registry"

func runResolve(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("resolve", flag.ContinueOnError)
	fs.SetOutput(stderr)
	registryDir := fs.String("registry", defaultRegistry, "directory holding the registry files")
	if err := fs.Parse(args); err != nil {
		return exitUsage
	}
	if fs.NArg() != 1 {
		return fail(stderr, exitUsage, "resolve takes exactly one project directory")
	}
	dir := fs.Arg(0)

	m, err := manifest.Load(filepath.Join(dir, manifest.FileName))
	if err != nil {
		return fail(stderr, exitUsage, "%v", err)
	}
	reg, err := registry.Load(*registryDir)
	if err != nil {
		return fail(stderr, exitUsage, "%v", err)
	}
	res, err := resolve.Resolve(m, reg)
	if err != nil {
		return fail(stderr, exitResolve, "%v", err)
	}
	if err := lockfile.Write(filepath.Join(dir, lockfile.FileName), lockfile.Build(m, res)); err != nil {
		return fail(stderr, exitUsage, "%v", err)
	}
	fmt.Fprintf(stdout, "resolved %d packages\n", len(res.Selected))
	return exitOK
}

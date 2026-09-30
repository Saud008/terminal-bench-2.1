package cli

import (
	"fmt"
	"io"

	"quire/internal/resolve"
	"quire/internal/version"
)

type options struct {
	confName string
	version  version.Request
	paths    []string
}

// parseArgs reads the options that precede the file paths. The first
// argument that is not an option starts the path list; everything after it
// is a path. It returns done=true with an exit code when quire should stop.
func parseArgs(argv []string, stdout, stderr io.Writer) (opts options, code int, done bool) {
	opts = options{confName: resolve.DefaultConfName, version: version.NoRequest}
	if len(argv) <= 1 {
		printVersion(stderr)
		printUsage(stderr, argv[0])
		return opts, 1, true
	}
	wantVersion, wantConf := false, false
	for i := 1; i < len(argv); i++ {
		arg := argv[i]
		switch {
		case wantVersion:
			wantVersion = false
			if !opts.version.Apply(arg) {
				fmt.Fprintf(stderr, "Invalid version number: %s\n", arg)
				return opts, 1, true
			}
		case wantConf:
			wantConf = false
			opts.confName = arg
		case arg == "--version" || arg == "-v":
			printVersion(stdout)
			return opts, 0, true
		case arg == "--help" || arg == "-h":
			printVersion(stdout)
			printUsage(stdout, argv[0])
			return opts, 0, true
		case arg == "-b":
			wantVersion = true
		case arg == "-f":
			wantConf = true
		default:
			opts.paths = argv[i:]
			i = len(argv)
		}
	}
	if len(opts.paths) == 0 {
		printUsage(stderr, argv[0])
		return opts, 1, true
	}
	return opts, 0, false
}

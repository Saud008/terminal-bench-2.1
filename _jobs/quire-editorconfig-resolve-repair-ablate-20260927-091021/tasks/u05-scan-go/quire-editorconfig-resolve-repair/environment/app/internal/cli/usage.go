package cli

import (
	"fmt"
	"io"

	"quire/internal/version"
)

func printVersion(w io.Writer) {
	fmt.Fprintf(w, "EditorConfig C Core Version %s\n", version.Current)
}

func printUsage(w io.Writer, command string) {
	fmt.Fprintf(w, "Usage: %s [OPTIONS] FILEPATH1 [FILEPATH2 FILEPATH3 ...]\n", command)
	fmt.Fprintf(w, "FILEPATH can be a hyphen (-) if you want to path(s) to be read from stdin.\n")
	fmt.Fprintf(w, "\n")
	fmt.Fprintf(w, "-f                 Specify conf filename other than \".editorconfig\".\n")
	fmt.Fprintf(w, "-b                 Specify version (used by devs to test compatibility).\n")
	fmt.Fprintf(w, "-h OR --help       Print this help message.\n")
	fmt.Fprintf(w, "-v OR --version    Display version information.\n")
}

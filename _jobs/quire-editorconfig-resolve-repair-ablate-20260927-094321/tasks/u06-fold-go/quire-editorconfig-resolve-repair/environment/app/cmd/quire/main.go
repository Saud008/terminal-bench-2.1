// Command quire prints the EditorConfig properties that apply to files.
package main

import (
	"os"

	"quire/internal/cli"
)

func main() {
	os.Exit(cli.Main(os.Args, os.Stdin, os.Stdout, os.Stderr))
}

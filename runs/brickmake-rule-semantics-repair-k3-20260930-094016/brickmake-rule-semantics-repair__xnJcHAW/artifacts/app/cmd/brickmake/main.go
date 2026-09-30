// Command brickmake is a GNU make compatible build tool for the subset of
// the makefile language described in docs/.
package main

import (
	"os"

	"brickmake/internal/cli"
)

func main() {
	os.Exit(cli.Main(os.Args[1:]))
}

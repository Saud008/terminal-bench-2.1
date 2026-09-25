package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/actplay/internal/replay"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: actplay export --scenario <path> --output <path>")
		os.Exit(2)
	}
	if os.Args[1] != "export" {
		fmt.Fprintf(os.Stderr, "unknown command: %s\n", os.Args[1])
		os.Exit(2)
	}
	fs := flag.NewFlagSet("export", flag.ExitOnError)
	scenario := fs.String("scenario", "", "scenario json path")
	output := fs.String("output", "", "export json path")
	_ = fs.Parse(os.Args[2:])
	if *scenario == "" || *output == "" {
		fmt.Fprintln(os.Stderr, "export requires --scenario and --output")
		os.Exit(2)
	}
	os.Exit(replay.ExportCLI(*scenario, *output))
}

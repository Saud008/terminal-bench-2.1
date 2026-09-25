package main

import (
	"fmt"
	"os"

	"github.com/terminus/collectdctl/internal/pipeline"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "ingest":
		textPath := flagVal("--text")
		cfgPath := flagVal("--config")
		outPath := flagVal("--output")
		if cfgPath == "" || outPath == "" {
			usage()
			os.Exit(2)
		}
		rc, err := pipeline.Run(textPath, cfgPath, outPath)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(rc)
		}
		os.Exit(rc)
	case "stage":
		textPath := flagVal("--text")
		cfgPath := flagVal("--config")
		if cfgPath == "" {
			usage()
			os.Exit(2)
		}
		if err := pipeline.Stage(textPath, cfgPath); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		os.Exit(0)
	case "export":
		outPath := flagVal("--output")
		if outPath == "" {
			usage()
			os.Exit(2)
		}
		rc, err := pipeline.Export(outPath)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(rc)
		}
		os.Exit(rc)
	default:
		fmt.Fprintln(os.Stderr, "unknown command")
		os.Exit(2)
	}
}

func flagVal(name string) string {
	for i, a := range os.Args {
		if a == name && i+1 < len(os.Args) {
			return os.Args[i+1]
		}
	}
	return ""
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage:")
	fmt.Fprintln(os.Stderr, "  collectdctl ingest --config PATH --output PATH [--text PATH]")
	fmt.Fprintln(os.Stderr, "  collectdctl stage --config PATH [--text PATH]")
	fmt.Fprintln(os.Stderr, "  collectdctl export --output PATH")
}

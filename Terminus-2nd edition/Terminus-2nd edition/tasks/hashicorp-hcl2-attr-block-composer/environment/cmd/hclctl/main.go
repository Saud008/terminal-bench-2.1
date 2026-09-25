package main

import (
	"fmt"
	"os"

	"github.com/terminus/hclmerge/internal/export"
	"github.com/terminus/hclmerge/internal/ingest"
	"github.com/terminus/hclmerge/internal/staging"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "ingest":
		if len(os.Args) != 3 {
			fmt.Fprintln(os.Stderr, "usage: hclctl ingest <fragments-dir>")
			os.Exit(2)
		}
		if err := ingest.IngestDirectory(os.Args[2], staging.DefaultStagePath); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case "merge":
		if len(os.Args) < 3 || os.Args[2] != "export" {
			fmt.Fprintln(os.Stderr, "usage: hclctl merge export")
			os.Exit(2)
		}
		if err := export.MergeExport(staging.DefaultStagePath, export.DefaultHCLPath, export.DefaultChecksumPath); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: hclctl ingest <fragments-dir> | hclctl merge export")
}

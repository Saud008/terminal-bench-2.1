package main

import (
	"fmt"
	"os"

	"github.com/terminus/layerfuse/internal/export"
	"github.com/terminus/layerfuse/internal/matpipe"
	"github.com/terminus/layerfuse/internal/tararchive"
	"github.com/terminus/layerfuse/internal/ledgerio"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "ingest":
		if len(os.Args) != 3 {
			fmt.Fprintln(os.Stderr, "usage: layerfuse ingest <stack-json>")
			os.Exit(2)
		}
		if err := tararchive.IngestStack(os.Args[2], ledgerio.DefaultStagePath, ledgerio.DefaultCommitPath); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case "materialize":
		if err := matpipe.Run(ledgerio.DefaultStagePath, ledgerio.DefaultStackPath); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case "manifest":
		if len(os.Args) < 3 || os.Args[2] != "export" {
			fmt.Fprintln(os.Stderr, "usage: layerfuse manifest export")
			os.Exit(2)
		}
		if err := export.ManifestExport(ledgerio.DefaultStackPath, ledgerio.DefaultCommitPath, export.DefaultOutputPath); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: layerfuse ingest <stack-json> | layerfuse materialize | layerfuse manifest export")
}

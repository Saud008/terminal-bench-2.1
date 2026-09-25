package main

import (
	"fmt"
	"os"

	"github.com/terminus/caddyctl/internal/export"
	"github.com/terminus/caddyctl/internal/ingest"
	"github.com/terminus/caddyctl/internal/matchcmd"
	"github.com/terminus/caddyctl/internal/staging"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "ingest":
		if len(os.Args) != 3 {
			fmt.Fprintln(os.Stderr, "usage: caddyctl ingest <routes-dir>")
			os.Exit(2)
		}
		if err := ingest.IngestDirectory(os.Args[2], staging.DefaultStagePath, staging.DefaultCommitPath); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case "match":
		reqFile := ""
		for i := 2; i < len(os.Args); i++ {
			if os.Args[i] == "--request" && i+1 < len(os.Args) {
				reqFile = os.Args[i+1]
				break
			}
		}
		if reqFile == "" {
			fmt.Fprintln(os.Stderr, "usage: caddyctl match --request <http-bytes-file>")
			os.Exit(2)
		}
		if err := matchcmd.Run(reqFile, staging.DefaultStagePath, staging.DefaultLastMatchPath); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case "route":
		if len(os.Args) < 3 || os.Args[2] != "export" {
			fmt.Fprintln(os.Stderr, "usage: caddyctl route export")
			os.Exit(2)
		}
		if err := export.RouteExport(staging.DefaultStagePath, staging.DefaultLastMatchPath, staging.DefaultCommitPath, export.DefaultOutputPath); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: caddyctl ingest <routes-dir> | caddyctl match --request <file> | caddyctl route export")
}

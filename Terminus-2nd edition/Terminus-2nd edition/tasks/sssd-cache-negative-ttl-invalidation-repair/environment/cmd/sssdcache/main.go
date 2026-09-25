package main

import (
	"fmt"
	"os"

	"github.com/terminus/sssdcache/internal/apperr"
	"github.com/terminus/sssdcache/internal/export"
	"github.com/terminus/sssdcache/internal/replay"
	"github.com/terminus/sssdcache/internal/staging"
	"github.com/terminus/sssdcache/internal/store"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(apperr.ExitError)
	}
	switch os.Args[1] {
	case "ingest":
		ops := flagVal("--ops")
		cfg := flagVal("--config")
		snap := flagVal("--snapshot")
		db := flagVal("--db")
		if ops == "" || cfg == "" {
			usage()
			os.Exit(apperr.ExitError)
		}
		if snap == "" {
			snap = staging.DefaultPath
		}
		if db == "" {
			db = store.DefaultDBPath
		}
		code, err := replay.Run(ops, cfg, snap, db)
		if err != nil {
			fmt.Fprintf(os.Stderr, "sssdcache: %v\n", err)
		}
		os.Exit(code)
	case "export":
		snapshot := flagVal("--snapshot")
		out := flagVal("--output")
		if snapshot == "" || out == "" {
			usage()
			os.Exit(apperr.ExitError)
		}
		if err := export.Publish(snapshot, out); err != nil {
			fmt.Fprintf(os.Stderr, "sssdcache: %v\n", err)
			os.Exit(apperr.ExitError)
		}
		os.Exit(apperr.ExitOK)
	default:
		usage()
		os.Exit(apperr.ExitError)
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
	fmt.Fprintf(os.Stderr, "usage:\n")
	fmt.Fprintf(os.Stderr, "  sssdcache ingest --ops <dir> --config <path> [--snapshot <path>] [--db <path>]\n")
	fmt.Fprintf(os.Stderr, "  sssdcache export --snapshot <path> --output <path>\n")
}

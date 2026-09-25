package main

import (
	"fmt"
	"os"

	"github.com/terminus/radiusproxy/internal/apperr"
	"github.com/terminus/radiusproxy/internal/export"
	"github.com/terminus/radiusproxy/internal/replay"
	"github.com/terminus/radiusproxy/internal/staging"
	"github.com/terminus/radiusproxy/internal/store"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(apperr.ExitError)
	}
	switch os.Args[1] {
	case "ingest":
		logs := flagVal("--logs")
		cfg := flagVal("--config")
		snap := flagVal("--snapshot")
		db := flagVal("--db")
		if logs == "" || cfg == "" {
			usage()
			os.Exit(apperr.ExitError)
		}
		if snap == "" {
			snap = staging.DefaultPath
		}
		if db == "" {
			db = store.DefaultDBPath
		}
		code, err := replay.Run(logs, cfg, snap, db)
		if err != nil {
			fmt.Fprintf(os.Stderr, "radiusproxy: %v\n", err)
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
			fmt.Fprintf(os.Stderr, "radiusproxy: %v\n", err)
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
	fmt.Fprintf(os.Stderr, "  radiusproxy ingest --logs <dir> --config <path> [--snapshot <path>] [--db <path>]\n")
	fmt.Fprintf(os.Stderr, "  radiusproxy export --snapshot <path> --output <path>\n")
}

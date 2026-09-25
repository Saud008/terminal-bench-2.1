package main

import (
	"fmt"
	"os"

	"github.com/clickparts/chparts/internal/export"
	"github.com/clickparts/chparts/internal/ingest"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "ingest":
		if err := runIngest(os.Args[2:]); err != nil {
			fmt.Fprintf(os.Stderr, "ingest: %v\n", err)
			os.Exit(1)
		}
	case "export":
		if err := runExport(os.Args[2:]); err != nil {
			fmt.Fprintf(os.Stderr, "export: %v\n", err)
			os.Exit(1)
		}
	case "read":
		if err := runIngest(os.Args[2:]); err != nil {
			fmt.Fprintf(os.Stderr, "read ingest: %v\n", err)
			os.Exit(1)
		}
		if err := runExport(os.Args[2:]); err != nil {
			fmt.Fprintf(os.Stderr, "read export: %v\n", err)
			os.Exit(1)
		}
	default:
		usage()
		os.Exit(2)
	}
}

func runIngest(args []string) error {
	partsDir := "/app/fixtures/parts"
	cfgPath := "/app/config/table.json"
	dbPath := "/app/data/parts.db"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--parts-dir":
			i++
			partsDir = args[i]
		case "--config":
			i++
			cfgPath = args[i]
		case "--db":
			i++
			dbPath = args[i]
		case "--output":
			i++
		}
	}
	return ingest.Run(partsDir, cfgPath, dbPath)
}

func runExport(args []string) error {
	output := "/app/output/parts-report.json"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--output":
			i++
			output = args[i]
		case "--parts-dir", "--config", "--db":
			i++
		}
	}
	return export.WriteReport(output)
}

func usage() {
	fmt.Fprintf(os.Stderr, "usage: chparts ingest|export|read [flags]\n")
}

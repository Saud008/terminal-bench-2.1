package main

import (
	"fmt"
	"os"

	"github.com/harbor/fix-session-replay-ledger/internal/export"
	"github.com/harbor/fix-session-replay-ledger/internal/ingest"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: fix-ledger <ingest|export> ...")
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "ingest":
		err = runIngest(os.Args[2:])
	case "export":
		err = runExport(os.Args[2:])
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func runIngest(args []string) error {
	sessionDir := ""
	dbPath := "/app/state/ledger.db"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--session-dir":
			i++
			if i >= len(args) {
				return fmt.Errorf("missing --session-dir")
			}
			sessionDir = args[i]
		case "--db":
			i++
			if i >= len(args) {
				return fmt.Errorf("missing --db")
			}
			dbPath = args[i]
		default:
			return fmt.Errorf("unknown flag: %s", args[i])
		}
	}
	if sessionDir == "" {
		return fmt.Errorf("--session-dir required")
	}
	return ingest.Run(sessionDir, dbPath)
}

func runExport(args []string) error {
	dbPath := "/app/state/ledger.db"
	outPath := "/app/output/positions.json"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--db":
			i++
			if i >= len(args) {
				return fmt.Errorf("missing --db")
			}
			dbPath = args[i]
		case "--out":
			i++
			if i >= len(args) {
				return fmt.Errorf("missing --out")
			}
			outPath = args[i]
		default:
			return fmt.Errorf("unknown flag: %s", args[i])
		}
	}
	return export.Run(dbPath, outPath)
}

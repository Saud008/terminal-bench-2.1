package main

import (
	"fmt"
	"os"

	_ "modernc.org/sqlite"

	"github.com/terminus/sqlitemigrate/internal/apply"
	"github.com/terminus/sqlitemigrate/internal/export"
	"github.com/terminus/sqlitemigrate/internal/ingest"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: migratectl apply <journal.jsonl> | export [--pass N]")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "apply":
		if len(os.Args) != 3 {
			fmt.Fprintln(os.Stderr, "usage: migratectl apply <journal.jsonl>")
			os.Exit(2)
		}
		if err := runApply(os.Args[2]); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case "export":
		pass := 1
		if len(os.Args) == 4 && os.Args[2] == "--pass" {
			if _, err := fmt.Sscanf(os.Args[3], "%d", &pass); err != nil {
				fmt.Fprintln(os.Stderr, "bad --pass value")
				os.Exit(2)
			}
		} else if len(os.Args) != 2 {
			fmt.Fprintln(os.Stderr, "usage: migratectl export [--pass N]")
			os.Exit(2)
		}
		if err := export.BuildLedger(dbPath(), stagePath(), export.DefaultLedgerPath, pass); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
}

func runApply(journalPath string) error {
	events, err := ingest.LoadJournal(journalPath)
	if err != nil {
		return err
	}
	db, err := apply.OpenDB(dbPath())
	if err != nil {
		return err
	}
	defer db.Close()
	return apply.ApplyJournal(db, events, stagePath())
}

func dbPath() string {
	if s := os.Getenv("TB3_DB_SUFFIX"); s != "" {
		return apply.DefaultDBPath + s
	}
	return apply.DefaultDBPath
}

func stagePath() string {
	if s := os.Getenv("TB3_DB_SUFFIX"); s != "" {
		return "/app/state/migrate-stage" + s + ".json"
	}
	return "/app/state/migrate-stage.json"
}

package main

import (
	"fmt"
	"os"

	"github.com/terminus/redisstream/internal/claim"
	"github.com/terminus/redisstream/internal/export"
	"github.com/terminus/redisstream/internal/ingest"
	"github.com/terminus/redisstream/internal/staging"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: redisctl replay <journal.jsonl> | export [--pass N]")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "replay":
		if len(os.Args) != 3 {
			fmt.Fprintln(os.Stderr, "usage: redisctl replay <journal.jsonl>")
			os.Exit(2)
		}
		if err := runReplay(os.Args[2]); err != nil {
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
			fmt.Fprintln(os.Stderr, "usage: redisctl export [--pass N]")
			os.Exit(2)
		}
		if err := export.BuildRollup(staging.DefaultStagePath, export.DefaultRollupPath, pass); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
}

func runReplay(journalPath string) error {
	events, err := ingest.LoadJournal(journalPath)
	if err != nil {
		return err
	}
	st := staging.NewEmpty()
	if err := claim.Replay(events, st); err != nil {
		return err
	}
	return staging.Save(staging.DefaultStagePath, st)
}

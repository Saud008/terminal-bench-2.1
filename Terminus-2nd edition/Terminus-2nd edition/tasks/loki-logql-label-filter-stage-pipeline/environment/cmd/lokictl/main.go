package main

import (
	"fmt"
	"os"

	"github.com/terminus/lokilogql/internal/export"
	"github.com/terminus/lokilogql/internal/ingest"
	"github.com/terminus/lokilogql/internal/pipeline"
	"github.com/terminus/lokilogql/internal/staging"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: lokictl eval --query <file> --lines <file> | export [--pass N]")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "eval":
		if err := runEval(os.Args[2:]); err != nil {
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
			fmt.Fprintln(os.Stderr, "usage: lokictl export [--pass N]")
			os.Exit(2)
		}
		if err := export.BuildFingerprint(staging.DefaultStagePath, export.DefaultFingerprintPath, pass); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
}

func runEval(args []string) error {
	var queryPath, linesPath string
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--query":
			if i+1 >= len(args) {
				return fmt.Errorf("missing --query value")
			}
			queryPath = args[i+1]
			i++
		case "--lines":
			if i+1 >= len(args) {
				return fmt.Errorf("missing --lines value")
			}
			linesPath = args[i+1]
			i++
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if queryPath == "" || linesPath == "" {
		return fmt.Errorf("usage: lokictl eval --query <file> --lines <file>")
	}
	raw, err := os.ReadFile(queryPath)
	if err != nil {
		return err
	}
	ast, err := ingest.ParseQuery(string(raw))
	if err != nil {
		return err
	}
	lines, err := ingest.LoadLines(linesPath)
	if err != nil {
		return err
	}
	st, err := pipeline.ExecuteEval(lines, ast)
	if err != nil {
		return err
	}
	return staging.Save(staging.DefaultStagePath, st)
}

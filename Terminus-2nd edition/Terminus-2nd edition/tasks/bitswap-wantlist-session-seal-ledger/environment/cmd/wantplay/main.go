package main

import (
	"fmt"
	"os"

	"wantplay/internal/orchestrator"
	"wantplay/internal/snapwriter"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "pipeline":
		os.Exit(runPipeline())
	case "metrics":
		os.Exit(runMetrics())
	default:
		usage()
		os.Exit(2)
	}
}

func runPipeline() int {
	logPath, session, stagingPath, outPath := "", "", snapwriter.DefaultPath, ""
	for i := 2; i < len(os.Args); i++ {
		switch os.Args[i] {
		case "--log":
			i++
			if i >= len(os.Args) {
				return 2
			}
			logPath = os.Args[i]
		case "--session":
			i++
			if i >= len(os.Args) {
				return 2
			}
			session = os.Args[i]
		case "--staging":
			i++
			if i >= len(os.Args) {
				return 2
			}
			stagingPath = os.Args[i]
		case "--output":
			i++
			if i >= len(os.Args) {
				return 2
			}
			outPath = os.Args[i]
		default:
			return 2
		}
	}
	if logPath == "" || session == "" || outPath == "" {
		return 2
	}
	if _, err := orchestrator.RunIngestStagingExport(logPath, session, stagingPath, outPath); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	return 0
}

func runMetrics() int {
	logPath, session, outPath := "", "", ""
	for i := 2; i < len(os.Args); i++ {
		switch os.Args[i] {
		case "--log":
			i++
			if i >= len(os.Args) {
				return 2
			}
			logPath = os.Args[i]
		case "--session":
			i++
			if i >= len(os.Args) {
				return 2
			}
			session = os.Args[i]
		case "--output":
			i++
			if i >= len(os.Args) {
				return 2
			}
			outPath = os.Args[i]
		default:
			return 2
		}
	}
	if logPath == "" || session == "" || outPath == "" {
		return 2
	}
	if err := orchestrator.RunMetricsReplay(logPath, session, outPath); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	return 0
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage:")
	fmt.Fprintln(os.Stderr, "  wantplay pipeline --log <jsonl> --session <name> --output <export.json> [--staging /app/state/want-snapshot.json]")
	fmt.Fprintln(os.Stderr, "  wantplay metrics --log <jsonl> --session <name> --output <metrics.json>")
}

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"github.com/terminus/cadence-replay/internal/parse"
	"github.com/terminus/cadence-replay/internal/replay"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: cadence-replay replay|dump-report")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "replay":
		runReplay(os.Args[2:])
	case "dump-report":
		runDumpReport(os.Args[2:])
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
}

func runReplay(args []string) {
	fs := flag.NewFlagSet("replay", flag.ExitOnError)
	scenarioPath := fs.String("scenario", "", "scenario JSON path")
	outputPath := fs.String("output", "/app/output/workflow-replay-report.json", "report JSON path")
	statePath := fs.String("state", "/app/state/cadence-task-state.json", "runtime state snapshot path")
	_ = fs.Parse(args)
	if *scenarioPath == "" {
		fmt.Fprintln(os.Stderr, "--scenario required")
		os.Exit(2)
	}
	sc, err := parse.LoadScenario(*scenarioPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	report := replay.Run(sc)
	if err := writeJSON(*outputPath, report); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	snap := map[string]any{
		"workflow_id":              report.WorkflowID,
		"visibility_deadline_ms":   report.VisibilityDeadlineMs,
		"last_progress_seq":        report.LastProgressSeq,
		"sticky_partition":         report.StickyPartition,
		"history_cursor_seq":       report.HistoryCursorSeq,
		"duplicate_events_skipped": report.DuplicateEventsSkipped,
		"decision_task_lost":       report.DecisionTaskLost,
		"timed_out":                report.TimedOut,
	}
	if err := writeJSON(*statePath, snap); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func runDumpReport(args []string) {
	fs := flag.NewFlagSet("dump-report", flag.ExitOnError)
	outputPath := fs.String("output", "/app/output/workflow-replay-report.json", "report JSON path")
	_ = fs.Parse(args)
	raw, err := os.ReadFile(*outputPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	var report map[string]any
	if err := json.Unmarshal(raw, &report); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	_ = enc.Encode(report)
}

func writeJSON(path string, v any) error {
	if err := os.MkdirAll(dirOf(path), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	return os.WriteFile(path, raw, 0o644)
}

func dirOf(path string) string {
	for i := len(path) - 1; i >= 0; i-- {
		if path[i] == '/' {
			return path[:i]
		}
	}
	return "."
}

package main

import (
	"flag"
	"fmt"
	"os"

	"mailindex/internal/export"
	"mailindex/internal/mailparse"
	"mailindex/internal/model"
	"mailindex/internal/staging"
	"mailindex/internal/store"
	"mailindex/internal/thread"
)

func main() {
	os.Exit(run())
}

func run() int {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "subcommand required")
		return 2
	}
	switch os.Args[1] {
	case "index":
		return runIndex(os.Args[2:])
	case "publish":
		return runPublish(os.Args[2:])
	default:
		return 2
	}
}

func runPublish(args []string) int {
	fs := flag.NewFlagSet("publish", flag.ExitOnError)
	out := fs.String("output", "", "")
	_ = fs.Parse(args)
	if *out == "" {
		return 2
	}
	if err := export.PublishReport(*out); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	return 0
}

func runIndex(args []string) int {
	fs := flag.NewFlagSet("index", flag.ExitOnError)
	dir := fs.String("mail-dir", "", "")
	dbPath := fs.String("thread-db", "", "")
	out := fs.String("output", "", "")
	_ = fs.Parse(args)
	if *dir == "" || *dbPath == "" || *out == "" {
		return 2
	}

	info, err := os.Stat(*dir)
	if err != nil || !info.IsDir() {
		return 2
	}

	msgs, filesRead, skipped, err := mailparse.LoadMailDir(*dir)
	if err != nil {
		return 2
	}

	stats := model.Stats{FilesRead: filesRead, MessagesSkippedMalformed: skipped}
	prepared := thread.Prepare(msgs, &stats)
	indexed := thread.AssignThreads(prepared, &stats)

	st, err := store.Open(*dbPath)
	if err != nil {
		return 1
	}
	defer st.Close()

	if err := st.Apply(indexed, &stats); err != nil {
		return 1
	}

	report := model.Report{
		IndexVersion:             1,
		FilesRead:                stats.FilesRead,
		MessagesIn:               stats.MessagesIn,
		MessagesIndexed:          stats.MessagesIndexed,
		MessagesSkippedMalformed: stats.MessagesSkippedMalformed,
		MessagesDeduped:          stats.MessagesDeduped,
		ThreadsResolved:          stats.ThreadsResolved,
		MessagesIndexedList:      indexed,
	}
	if err := staging.WriteIndexSnapshot(*dbPath, report); err != nil {
		return 1
	}
	if err := export.PublishReport(*out); err != nil {
		return 1
	}
	return 0
}

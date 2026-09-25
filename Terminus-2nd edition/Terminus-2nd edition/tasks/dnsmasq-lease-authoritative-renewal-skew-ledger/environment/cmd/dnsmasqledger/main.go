package main

import (
	"fmt"
	"os"

	"dnsmasqledger/internal/export"
	"dnsmasqledger/internal/replay"
	"dnsmasqledger/internal/store"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: dnsmasqledger replay --log <path> --output <path> --db <path>")
		os.Exit(2)
	}
	if os.Args[1] != "replay" {
		fmt.Fprintln(os.Stderr, "unknown command")
		os.Exit(2)
	}
	var logPath, outPath, dbPath string
	for i := 2; i < len(os.Args); i++ {
		switch os.Args[i] {
		case "--log":
			i++
			logPath = os.Args[i]
		case "--output":
			i++
			outPath = os.Args[i]
		case "--db":
			i++
			dbPath = os.Args[i]
		}
	}
	if logPath == "" || outPath == "" || dbPath == "" {
		fmt.Fprintln(os.Stderr, "missing required flags")
		os.Exit(2)
	}
	if err := store.VerifyPath(dbPath); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	cat, applied, err := replay.Run(logPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := export.WriteSnapshot(cat); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	rep := export.BuildReport(cat, applied)
	if err := export.WriteReport(outPath, rep); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := store.Persist(dbPath, cat); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

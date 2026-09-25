package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/vicireplay/internal/capture"
	"github.com/terminus/vicireplay/internal/export"
	"github.com/terminus/vicireplay/internal/replay"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "replay":
		fs := flag.NewFlagSet("replay", flag.ExitOnError)
		tracePath := fs.String("trace", "", "vici jsonl trace")
		output := fs.String("output", "/app/output/rekey-report.json", "report path")
		_ = fs.Parse(os.Args[2:])
		if *tracePath == "" {
			fmt.Fprintln(os.Stderr, "missing --trace")
			os.Exit(2)
		}
		tr, err := capture.LoadTrace(*tracePath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "load trace: %v\n", err)
			os.Exit(1)
		}
		res, err := replay.Run(tr)
		if err != nil {
			fmt.Fprintf(os.Stderr, "replay: %v\n", err)
			os.Exit(1)
		}
		if err := export.WriteReport(*output, res.RekeyRejectCount); err != nil {
			fmt.Fprintf(os.Stderr, "export: %v\n", err)
			os.Exit(1)
		}
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: vicireplay replay --trace PATH --output PATH")
}

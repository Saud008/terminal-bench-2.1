package main

import (
	"flag"
	"fmt"
	"os"
	"strings"

	"github.com/terminus/cdcctl/internal/roll"
)

func main() {
	if len(os.Args) < 2 || os.Args[1] != "roll" {
		fmt.Fprintln(os.Stderr, "usage: cdcctl roll --input PATH --seed SEED [--output PATH] [--checkpoint PATH] [--resume] [--max-chunks N]")
		os.Exit(2)
	}

	fs := flag.NewFlagSet("roll", flag.ExitOnError)
	input := fs.String("input", "", "input binary path")
	seed := fs.String("seed", "", "roll seed")
	output := fs.String("output", "", "output JSON path")
	checkpointPath := fs.String("checkpoint", "", "checkpoint JSON path")
	resume := fs.Bool("resume", false, "resume from checkpoint")
	maxChunks := fs.Int("max-chunks", 0, "stop after N chunks")
	_ = fs.Parse(os.Args[2:])

	if *input == "" || *seed == "" {
		fmt.Fprintln(os.Stderr, "usage: cdcctl roll --input PATH --seed SEED [--output PATH] [--checkpoint PATH] [--resume] [--max-chunks N]")
		os.Exit(2)
	}

	_, err := roll.Roll(roll.Options{
		InputPath:      *input,
		Seed:           *seed,
		OutputPath:     *output,
		CheckpointPath: *checkpointPath,
		Resume:         *resume,
		MaxChunks:      *maxChunks,
	})
	if err != nil {
		if strings.Contains(err.Error(), "invalid") {
			os.Exit(1)
		}
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

package main

import (
	"fmt"
	"os"

	"github.com/terminus/fixdropcopy/internal/export"
	"github.com/terminus/fixdropcopy/internal/ingest"
	"github.com/terminus/fixdropcopy/internal/replay"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "ingest":
		err = runIngest(os.Args[2:])
	case "replay":
		err = runReplay(os.Args[2:])
	case "export":
		err = runExport(os.Args[2:])
	default:
		usage()
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "dropcopyctl ingest --seed S --scenario NAME [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "dropcopyctl replay --scenario NAME")
	fmt.Fprintln(os.Stderr, "dropcopyctl export --scenario NAME --output PATH [--fixture-dir D]")
}

func runIngest(args []string) error {
	seed, scenario, fixtureDir := "", "", "/app/fixtures"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--seed":
			i++
			seed = args[i]
		case "--scenario":
			i++
			scenario = args[i]
		case "--fixture-dir":
			i++
			fixtureDir = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if seed == "" || scenario == "" {
		return fmt.Errorf("--seed and --scenario required")
	}
	return ingest.Run(seed, scenario, fixtureDir)
}

func runReplay(args []string) error {
	scenario := ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--scenario":
			i++
			scenario = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if scenario == "" {
		return fmt.Errorf("--scenario required")
	}
	return replay.Run(scenario)
}

func runExport(args []string) error {
	scenario, out := "", "/app/output/compliance.json"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--scenario":
			i++
			scenario = args[i]
		case "--output":
			i++
			out = args[i]
		case "--fixture-dir":
			// Accepted for CLI parity with ingest overlays; export does not re-read fixtures.
			i++
			_ = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if scenario == "" {
		return fmt.Errorf("--scenario required")
	}
	return export.Run(scenario, out)
}

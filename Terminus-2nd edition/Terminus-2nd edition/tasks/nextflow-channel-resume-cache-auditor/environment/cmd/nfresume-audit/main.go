package main

import (
	"fmt"
	"os"

	"github.com/terminus/nfresume/internal/audit"
	"github.com/terminus/nfresume/internal/export"
	"github.com/terminus/nfresume/internal/ingest"
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
	case "audit":
		err = runAudit(os.Args[2:])
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
	fmt.Fprintln(os.Stderr, "nfresume-audit ingest --seed S --scenario NAME [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "nfresume-audit audit --scenario NAME")
	fmt.Fprintln(os.Stderr, "nfresume-audit export --scenario NAME --output PATH")
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

func runAudit(args []string) error {
	scenario := ""
	for i := 0; i < len(args); i++ {
		if args[i] == "--scenario" {
			i++
			scenario = args[i]
		}
	}
	if scenario == "" {
		return fmt.Errorf("--scenario required")
	}
	return audit.Run(scenario)
}

func runExport(args []string) error {
	scenario, out := "", "/app/output/unsafe-cache-report.json"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--scenario":
			i++
			scenario = args[i]
		case "--output":
			i++
			out = args[i]
		}
	}
	if scenario == "" {
		return fmt.Errorf("--scenario required")
	}
	return export.Run(scenario, out)
}

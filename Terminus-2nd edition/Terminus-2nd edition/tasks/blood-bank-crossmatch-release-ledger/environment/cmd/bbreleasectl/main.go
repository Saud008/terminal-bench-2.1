package main

import (
	"fmt"
	"os"

	"github.com/terminus/bbreleasectl/internal/orchestrate"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "import-panels":
		err = runLoad(os.Args[2:])
	case "score-compatibility":
		err = runEvaluate(os.Args[2:])
	case "seal-releases":
		err = runPublish(os.Args[2:])
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
	fmt.Fprintln(os.Stderr, "bbreleasectl import-panels --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "bbreleasectl score-compatibility --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "bbreleasectl seal-releases --scenario SCENARIO [--output PATH]")
}

func runLoad(args []string) error {
	scenario, fixtureDir := "", "/app/fixtures"
	for i := 0; i < len(args); i++ {
		switch args[i] {
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
	if scenario == "" {
		return fmt.Errorf("--scenario required")
	}
	return orchestrate.LoadScenario(scenario, fixtureDir)
}

func runEvaluate(args []string) error {
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
	return orchestrate.EvaluateCrossmatch(scenario)
}

func runPublish(args []string) error {
	scenario, out := "", ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--scenario":
			i++
			scenario = args[i]
		case "--output":
			i++
			out = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if scenario == "" {
		return fmt.Errorf("--scenario required")
	}
	return orchestrate.PublishLedger(scenario, out)
}

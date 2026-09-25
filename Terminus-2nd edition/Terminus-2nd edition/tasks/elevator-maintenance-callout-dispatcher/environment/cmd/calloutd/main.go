package main

import (
	"fmt"
	"os"

	"github.com/terminus/calloutd/internal/dispatchorchestrator"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "load-roster":
		err = runLoad(args[2:])
	case "rank-faults":
		err = runRank(args[2:])
	case "bind-roster":
		err = runBind(args[2:])
	case "emit-callout":
		err = runEmit(args[2:])
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
	fmt.Fprintln(os.Stderr, "calloutd load-roster --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "calloutd rank-faults --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "calloutd bind-roster --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "calloutd emit-callout --scenario SCENARIO [--output PATH]")
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
	return dispatchorchestrator.LoadRoster(scenario, fixtureDir)
}

func runRank(args []string) error {
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
	return dispatchorchestrator.RankFaults(scenario)
}

func runBind(args []string) error {
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
	return dispatchorchestrator.BindRoster(scenario)
}

func runEmit(args []string) error {
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
	return dispatchorchestrator.EmitCallout(scenario, out)
}

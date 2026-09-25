package main

import (
	"fmt"
	"os"

	"github.com/terminus/mpiqctl/internal/orchestrator"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "snapshot-load":
		err = runLoad(argsSlice(2))
	case "compile-policy":
		err = runScenario("compile-policy", argsSlice(2), orchestrator.CompilePolicy)
	case "apply-holds":
		err = runScenario("apply-holds", argsSlice(2), orchestrator.ApplyHolds)
	case "filter-blackouts":
		err = runScenario("filter-blackouts", argsSlice(2), orchestrator.FilterBlackouts)
	case "score-queue":
		err = runScenario("score-queue", argsSlice(2), orchestrator.ScoreQueue)
	case "bind-inspectors":
		err = runScenario("bind-inspectors", argsSlice(2), orchestrator.BindInspectors)
	case "publish-queue":
		err = runPublish(argsSlice(2))
	default:
		usage()
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func argsSlice(n int) []string {
	if n >= len(os.Args) {
		return nil
	}
	return os.Args[n:]
}

func usage() {
	fmt.Fprintln(os.Stderr, "mpiqctl snapshot-load --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "mpiqctl compile-policy --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "mpiqctl apply-holds --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "mpiqctl filter-blackouts --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "mpiqctl score-queue --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "mpiqctl bind-inspectors --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "mpiqctl publish-queue --scenario SCENARIO [--output PATH]")
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
	return orchestrator.SnapshotLoad(scenario, fixtureDir)
}

type scenarioFn func(string) error

func runScenario(name string, args []string, fn scenarioFn) error {
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
	_ = name
	return fn(scenario)
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
	return orchestrator.PublishQueue(scenario, out)
}

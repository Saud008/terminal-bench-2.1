package main

import (
	"fmt"
	"os"

	"github.com/terminus/whslot/internal/atlasemit"
	"github.com/terminus/whslot/internal/runbook"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "latch-yard":
		err = runLoad(os.Args[2:])
	case "score-skus":
		err = runbook.RankVelocity()
	case "draft-wave":
		err = runbook.PlanReplen()
	case "crew-bind":
		err = runbook.BindShifts()
	case "emit-atlas":
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
	fmt.Fprintln(os.Stderr, "whslot latch-yard --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "whslot score-skus")
	fmt.Fprintln(os.Stderr, "whslot draft-wave")
	fmt.Fprintln(os.Stderr, "whslot crew-bind")
	fmt.Fprintln(os.Stderr, "whslot emit-atlas [--output PATH]")
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
	return runbook.LatchYard(scenario, fixtureDir)
}

func runPublish(args []string) error {
	out := ""
	for i := 0; i < len(args); i++ {
		if args[i] == "--output" {
			i++
			out = args[i]
		}
	}
	return atlasemit.Publish(out)
}

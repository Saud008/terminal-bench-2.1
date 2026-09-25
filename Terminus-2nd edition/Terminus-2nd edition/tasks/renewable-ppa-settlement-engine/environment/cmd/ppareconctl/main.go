package main

import (
	"fmt"
	"os"

	"github.com/terminus/ppareconctl/internal/pipeline"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "materialize-lines":
		err = runMaterializeLines(os.Args[2:])
	case "rollup-billing-invoice":
		err = runRollupBillingInvoice(os.Args[2:])
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
	fmt.Fprintln(os.Stderr, "ppareconctl materialize-lines --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "ppareconctl rollup-billing-invoice --scenario SCENARIO [--fixture-dir D]")
}

func runMaterializeLines(args []string) error {
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
	return pipeline.MaterializeLines(scenario, fixtureDir)
}

func runRollupBillingInvoice(args []string) error {
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
	return pipeline.RollupBillingInvoice(scenario, fixtureDir)
}

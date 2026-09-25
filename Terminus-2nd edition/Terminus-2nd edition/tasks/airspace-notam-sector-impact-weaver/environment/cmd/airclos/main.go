package main

import (
	"fmt"
	"os"

	"github.com/terminus/airclos/internal/labwire"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "bind-campaign":
		err = runBindCampaign(os.Args[2:])
	case "close-chronology":
		err = runCloseChronology(os.Args[2:])
	case "fold-closure":
		err = runFoldClosure(os.Args[2:])
	case "seal-atlas":
		err = runSealAtlas(os.Args[2:])
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
	fmt.Fprintln(os.Stderr, "airclos bind-campaign --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "airclos close-chronology --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "airclos fold-closure --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "airclos seal-atlas --scenario SCENARIO [--output PATH]")
}

func runBindCampaign(args []string) error {
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
	binding, err := labwire.BindCampaign(scenario, fixtureDir)
	if err != nil {
		return err
	}
	return labwire.PersistBinding(binding)
}

func runCloseChronology(args []string) error {
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
	return labwire.RunCloseChronology(scenario)
}

func runFoldClosure(args []string) error {
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
	return labwire.RunFoldClosure(scenario)
}

func runSealAtlas(args []string) error {
	scenario, outPath := "", ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--scenario":
			i++
			scenario = args[i]
		case "--output":
			i++
			outPath = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if scenario == "" {
		return fmt.Errorf("--scenario required")
	}
	return labwire.SealAtlas(scenario, outPath)
}

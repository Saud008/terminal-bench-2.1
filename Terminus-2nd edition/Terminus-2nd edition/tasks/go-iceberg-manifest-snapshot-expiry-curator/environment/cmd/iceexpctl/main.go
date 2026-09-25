package main

import (
	"fmt"
	"os"

	"github.com/terminus/iceexpctl/internal/icebridge"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "capture-catalog":
		err = runCaptureCatalog(os.Args[2:])
	case "audit-retention":
		err = runAuditRetention(os.Args[2:])
	case "publish-expiry":
		err = runPublishExpiry(os.Args[2:])
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
	fmt.Fprintln(os.Stderr, "iceexpctl capture-catalog --catalog NAME --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "iceexpctl audit-retention --catalog NAME --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "iceexpctl publish-expiry --catalog NAME --scenario SCENARIO [--plan-out PATH] [--orphan-out PATH]")
}

func runCaptureCatalog(args []string) error {
	catalog, scenario, fixtureDir := "", "", "/app/fixtures"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--catalog":
			i++
			catalog = args[i]
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
	if catalog == "" || scenario == "" {
		return fmt.Errorf("--catalog and --scenario required")
	}
	stage, err := icebridge.MaterializeTable(scenario, fixtureDir)
	if err != nil {
		return err
	}
	if stage.Table.TableName != catalog {
		return fmt.Errorf("catalog %s does not match table metadata %s", catalog, stage.Table.TableName)
	}
	return icebridge.PersistCursor(stage)
}

func runAuditRetention(args []string) error {
	catalog, scenario := "", ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--catalog":
			i++
			catalog = args[i]
		case "--scenario":
			i++
			scenario = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	_ = catalog
	if scenario == "" {
		return fmt.Errorf("--scenario required")
	}
	return icebridge.RunAnalyzePass(scenario)
}

func runPublishExpiry(args []string) error {
	catalog, scenario := "", ""
	planOut, orphanOut := "", ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--catalog":
			i++
			catalog = args[i]
		case "--scenario":
			i++
			scenario = args[i]
		case "--plan-out":
			i++
			planOut = args[i]
		case "--orphan-out":
			i++
			orphanOut = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	_ = catalog
	if scenario == "" {
		return fmt.Errorf("--scenario required")
	}
	return icebridge.SealExpiryPlan(scenario, planOut, orphanOut)
}

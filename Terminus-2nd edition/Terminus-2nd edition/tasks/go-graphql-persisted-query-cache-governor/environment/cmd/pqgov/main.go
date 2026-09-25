package main

import (
	"fmt"
	"os"

	"github.com/terminus/pqgov/internal/pqcli"
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
	case "reconcile":
		err = runReconcile(os.Args[2:])
	case "export-audit":
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
	fmt.Fprintln(os.Stderr, "pqgov ingest --tenant TENANT --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "pqgov reconcile --tenant TENANT --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "pqgov export-audit --tenant TENANT --scenario SCENARIO [--output PATH]")
}

func runIngest(args []string) error {
	tenant, scenario, fixtureDir := "", "", "/app/fixtures"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--tenant":
			i++
			tenant = args[i]
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
	if tenant == "" || scenario == "" {
		return fmt.Errorf("--tenant and --scenario required")
	}
	return pqcli.IngestTenant(tenant, scenario, fixtureDir)
}

func runReconcile(args []string) error {
	tenant, scenario, fixtureDir := "", "", "/app/fixtures"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--tenant":
			i++
			tenant = args[i]
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
	if tenant == "" || scenario == "" {
		return fmt.Errorf("--tenant and --scenario required")
	}
	return pqcli.ReconcileTenant(tenant, scenario, fixtureDir)
}

func runExport(args []string) error {
	tenant, scenario, output := "", "", ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--tenant":
			i++
			tenant = args[i]
		case "--scenario":
			i++
			scenario = args[i]
		case "--output":
			i++
			output = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if tenant == "" || scenario == "" {
		return fmt.Errorf("--tenant and --scenario required")
	}
	return pqcli.ExportAuditTenant(tenant, scenario, output)
}

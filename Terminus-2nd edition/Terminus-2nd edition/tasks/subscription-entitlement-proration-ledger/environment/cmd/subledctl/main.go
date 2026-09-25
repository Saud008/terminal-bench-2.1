package main

import (
    "fmt"
    "os"

    "github.com/terminus/subledctl/internal/workflowglue"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "load-cycle":
        err = runLoadCycle(os.Args[2:])
    case "reconcile-entitlements":
        err = runReconcile(os.Args[2:])
    case "publish-invoices":
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
    fmt.Fprintln(os.Stderr, "subledctl load-cycle --scenario SCENARIO [--fixture-dir D]")
    fmt.Fprintln(os.Stderr, "subledctl reconcile-entitlements --scenario SCENARIO")
    fmt.Fprintln(os.Stderr, "subledctl publish-invoices --scenario SCENARIO [--output PATH]")
}

func runLoadCycle(args []string) error {
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
    return workflowglue.LoadCycle(scenario, fixtureDir)
}

func runReconcile(args []string) error {
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
    return workflowglue.RunEntitlementPassCmd(scenario)
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
    return workflowglue.PublishInvoices(scenario, out)
}

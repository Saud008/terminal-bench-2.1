package main

import (
    "fmt"
    "os"

    "github.com/terminus/auctctl/internal/workflowglue"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "load-catalog":
        err = runLoad(os.Args[2:])
    case "adjudicate-lots":
        err = runAdjudicate(os.Args[2:])
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
    fmt.Fprintln(os.Stderr, "auctctl load-catalog --scenario SCENARIO [--fixture-dir D]")
    fmt.Fprintln(os.Stderr, "auctctl adjudicate-lots --scenario SCENARIO")
    fmt.Fprintln(os.Stderr, "auctctl publish-invoices --scenario SCENARIO [--output PATH]")
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
    return workflowglue.LoadCatalog(scenario, fixtureDir)
}

func runAdjudicate(args []string) error {
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
    return workflowglue.AdjudicateLots(scenario)
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

package main

import (
    "fmt"
    "os"

    "github.com/terminus/wfhistctl/internal/pipeline"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "ingest-history":
        err = runIngest(os.Args[2:])
    case "compact-summary":
        err = runCompact(os.Args[2:])
    case "emit-inspect":
        err = runEmit(os.Args[2:])
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
    fmt.Fprintln(os.Stderr, "wfhistctl ingest-history --namespace N --scenario S [--fixture-dir D]")
    fmt.Fprintln(os.Stderr, "wfhistctl compact-summary --namespace N --scenario S")
    fmt.Fprintln(os.Stderr, "wfhistctl emit-inspect --namespace N --scenario S [--output-db PATH] [--output-risk PATH]")
}

func runIngest(args []string) error {
    ns, scenario, fixtureDir := "", "", "/app/fixtures"
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--namespace":
            i++
            ns = args[i]
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
    if ns == "" || scenario == "" {
        return fmt.Errorf("--namespace and --scenario required")
    }
    snap, err := pipeline.MaterializeHistory(ns, scenario, fixtureDir)
    if err != nil {
        return err
    }
    return pipeline.PersistStaging(snap)
}

func runCompact(args []string) error {
    ns, scenario := "", ""
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--namespace":
            i++
            ns = args[i]
        case "--scenario":
            i++
            scenario = args[i]
        default:
            return fmt.Errorf("unknown flag %s", args[i])
        }
    }
    _ = ns
    if scenario == "" {
        return fmt.Errorf("--scenario required")
    }
    return pipeline.RunCompactPass(scenario)
}

func runEmit(args []string) error {
    ns, scenario := "", ""
    dbOut, riskOut := "", ""
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--namespace":
            i++
            ns = args[i]
        case "--scenario":
            i++
            scenario = args[i]
        case "--output-db":
            i++
            dbOut = args[i]
        case "--output-risk":
            i++
            riskOut = args[i]
        default:
            return fmt.Errorf("unknown flag %s", args[i])
        }
    }
    if ns == "" || scenario == "" {
        return fmt.Errorf("--namespace and --scenario required")
    }
    return pipeline.EmitInspection(ns, scenario, dbOut, riskOut)
}

package main

import (
    "fmt"
    "os"

    "github.com/terminus/oidcgov/internal/governorbridge"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "load-transcript":
        err = runLoadTranscript(os.Args[2:])
    case "hydrate-cache":
        err = runHydrateCache(os.Args[2:])
    case "decide-batch":
        err = runDecideBatch(os.Args[2:])
    case "emit-report":
        err = runEmitReport(os.Args[2:])
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
    fmt.Fprintln(os.Stderr, "oidcgov load-transcript --scenario SCENARIO [--fixture-dir D]")
    fmt.Fprintln(os.Stderr, "oidcgov hydrate-cache --scenario SCENARIO")
    fmt.Fprintln(os.Stderr, "oidcgov decide-batch --scenario SCENARIO")
    fmt.Fprintln(os.Stderr, "oidcgov emit-report --scenario SCENARIO [--output PATH]")
}

func runLoadTranscript(args []string) error {
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
    stage, err := governorbridge.MaterializeTranscript(scenario, fixtureDir)
    if err != nil {
        return err
    }
    return governorbridge.PersistTranscript(stage)
}

func runHydrateCache(args []string) error {
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
    return governorbridge.RunHydratePass(scenario)
}

func runDecideBatch(args []string) error {
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
    return governorbridge.RunDecideBatch(scenario)
}

func runEmitReport(args []string) error {
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
    return governorbridge.SealGovernanceReport(scenario, outPath)
}

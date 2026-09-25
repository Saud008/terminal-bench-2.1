package main

import (
    "fmt"
    "os"

    "github.com/terminus/filingatlas/internal/nxtg11"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "load-bundle":
        err = runLoadBundle(os.Args[2:])
    case "index-parties":
        err = runIndexParties(os.Args[2:])
    case "scan-risks":
        err = runScanRisks(os.Args[2:])
    case "emit-atlas":
        err = runEmitAtlas(os.Args[2:])
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
    fmt.Fprintln(os.Stderr, "filingatlas load-bundle --scenario SCENARIO [--fixture-dir D]")
    fmt.Fprintln(os.Stderr, "filingatlas index-parties --scenario SCENARIO")
    fmt.Fprintln(os.Stderr, "filingatlas scan-risks --scenario SCENARIO")
    fmt.Fprintln(os.Stderr, "filingatlas emit-atlas --scenario SCENARIO [--output PATH]")
}

func runLoadBundle(args []string) error {
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
    stage, err := filingbridge.MaterializeBundle(scenario, fixtureDir)
    if err != nil {
        return err
    }
    return filingbridge.PersistBundle(stage)
}

func runIndexParties(args []string) error {
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
    return filingbridge.RunIndexParties(scenario)
}

func runScanRisks(args []string) error {
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
    return filingbridge.RunScanRisks(scenario)
}

func runEmitAtlas(args []string) error {
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
    return filingbridge.SealAtlasReport(scenario, outPath)
}

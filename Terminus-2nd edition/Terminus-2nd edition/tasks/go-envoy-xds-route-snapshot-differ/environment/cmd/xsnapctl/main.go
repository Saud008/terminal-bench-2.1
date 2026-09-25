package main

import (
    "fmt"
    "os"

    "github.com/terminus/xsnapctl/internal/xdsbridge"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "ingest-pair":
        err = runLoad(os.Args[2:])
    case "canonicalize":
        err = runNormalize(os.Args[2:])
    case "publish-diff":
        err = runEmitDiff(os.Args[2:])
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
    fmt.Fprintln(os.Stderr, "xsnapctl ingest-pair --scenario SCENARIO [--fixture-dir D]")
    fmt.Fprintln(os.Stderr, "xsnapctl canonicalize --scenario SCENARIO")
    fmt.Fprintln(os.Stderr, "xsnapctl publish-diff --scenario SCENARIO [--output PATH]")
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
    snap, err := xdsbridge.MaterializePair(scenario, fixtureDir)
    if err != nil {
        return err
    }
    return xdsbridge.PersistStaging(snap)
}

func runNormalize(args []string) error {
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
    return xdsbridge.RunNormalizePass(scenario)
}

func runEmitDiff(args []string) error {
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
    return xdsbridge.SealDiffReport(scenario, outPath)
}

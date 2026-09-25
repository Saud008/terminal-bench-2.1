package main

import (
    "fmt"
    "os"

    "github.com/terminus/spiffectl/internal/spiffebridge"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "bind-pair":
        err = runBindPair(os.Args[2:])
    case "normalize-trust":
        err = runNormalizeTrust(os.Args[2:])
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
    fmt.Fprintln(os.Stderr, "spiffectl bind-pair --scenario SCENARIO [--fixture-dir D]")
    fmt.Fprintln(os.Stderr, "spiffectl normalize-trust --scenario SCENARIO")
    fmt.Fprintln(os.Stderr, "spiffectl emit-atlas --scenario SCENARIO [--output PATH]")
}

func runBindPair(args []string) error {
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
    stage, err := spiffebridge.BindPairBundles(scenario, fixtureDir)
    if err != nil {
        return err
    }
    return spiffebridge.PersistCapture(stage)
}

func runNormalizeTrust(args []string) error {
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
    return spiffebridge.RunNormalizePass(scenario)
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
    return spiffebridge.SealAtlasReport(scenario, outPath)
}

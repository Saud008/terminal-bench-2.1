package main

import (
    "fmt"
    "os"

    "github.com/terminus/formulatrix/internal/formbridge"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "load-scenario":
        err = runLoadScenario(os.Args[2:])
    case "refresh-db":
        err = runRefreshDB(os.Args[2:])
    case "publish-matrix":
        err = runPublishMatrix(os.Args[2:])
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
    fmt.Fprintln(os.Stderr, "formulatrix load-scenario --scenario SCENARIO [--fixture-dir D] [--as-of DATE]")
    fmt.Fprintln(os.Stderr, "formulatrix refresh-db --scenario SCENARIO")
    fmt.Fprintln(os.Stderr, "formulatrix publish-matrix --scenario SCENARIO [--output PATH]")
}

func runLoadScenario(args []string) error {
    scenario, fixtureDir, asOf := "", "/app/fixtures", ""
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--scenario":
            i++
            scenario = args[i]
        case "--fixture-dir":
            i++
            fixtureDir = args[i]
        case "--as-of":
            i++
            asOf = args[i]
        default:
            return fmt.Errorf("unknown flag %s", args[i])
        }
    }
    if scenario == "" {
        return fmt.Errorf("--scenario required")
    }
    stage, err := formbridge.MaterializeScenario(scenario, fixtureDir, asOf)
    if err != nil {
        return err
    }
    return formbridge.PersistRoster(stage)
}

func runRefreshDB(args []string) error {
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
    return formbridge.RunRefreshPass(scenario)
}

func runPublishMatrix(args []string) error {
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
    return formbridge.SealMatrixPublish(scenario, outPath)
}

package main

import (
    "fmt"
    "os"

    "github.com/terminus/snapretctl/internal/csibridge"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "import-graph":
        err = runImportGraph(os.Args[2:])
    case "score-retention":
        err = runScoreRetention(os.Args[2:])
    case "publish-audit":
        err = runPublishAudit(os.Args[2:])
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
    fmt.Fprintln(os.Stderr, "snapretctl import-graph --scenario SCENARIO [--fixture-dir D]")
    fmt.Fprintln(os.Stderr, "snapretctl score-retention --scenario SCENARIO")
    fmt.Fprintln(os.Stderr, "snapretctl publish-audit --scenario SCENARIO [--output-report PATH] [--output-dangling PATH]")
}

func runImportGraph(args []string) error {
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
    stage, err := csibridge.MaterializeFleetGraph(scenario, fixtureDir)
    if err != nil {
        return err
    }
    return csibridge.PersistFleetGraph(stage)
}

func runScoreRetention(args []string) error {
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
    return csibridge.RunAnalyzePass(scenario)
}

func runPublishAudit(args []string) error {
    scenario := ""
    reportOut, danglingOut := "", ""
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--scenario":
            i++
            scenario = args[i]
        case "--output-report":
            i++
            reportOut = args[i]
        case "--output-dangling":
            i++
            danglingOut = args[i]
        default:
            return fmt.Errorf("unknown flag %s", args[i])
        }
    }
    if scenario == "" {
        return fmt.Errorf("--scenario required")
    }
    return csibridge.SealRetentionReport(scenario, reportOut, danglingOut)
}

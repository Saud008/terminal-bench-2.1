package main

import (
    "fmt"
    "os"

    "github.com/edgeiot/mqttsessctl/internal/mqttkernel"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "ingest-journal":
        err = runIngest(os.Args[2:])
    case "merge-session":
        err = runReconcile(os.Args[2:])
    case "emit-atlas":
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
    fmt.Fprintln(os.Stderr, "mqttsessctl ingest-journal --broker B --scenario S [--fixture-dir D]")
    fmt.Fprintln(os.Stderr, "mqttsessctl merge-session --broker B --scenario S")
    fmt.Fprintln(os.Stderr, "mqttsessctl emit-atlas --broker B --scenario S [--output-atlas PATH] [--output-ledger PATH]")
}

func runIngest(args []string) error {
    broker, scenario, fixtureDir := "", "", "/app/fixtures"
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--broker":
            i++
            broker = args[i]
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
    if broker == "" || scenario == "" {
        return fmt.Errorf("--broker and --scenario required")
    }
    snap, err := mqttkernel.LoadBrokerJournal(broker, scenario, fixtureDir)
    if err != nil {
        return err
    }
    return mqttkernel.WriteJournalStaging(snap)
}

func runReconcile(args []string) error {
    broker, scenario := "", ""
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--broker":
            i++
            broker = args[i]
        case "--scenario":
            i++
            scenario = args[i]
        default:
            return fmt.Errorf("unknown flag %s", args[i])
        }
    }
    _ = broker
    if scenario == "" {
        return fmt.Errorf("--scenario required")
    }
    return mqttkernel.RunMergePass(broker, scenario)
}

func runEmit(args []string) error {
    broker, scenario := "", ""
    atlasOut, ledgerOut := "", ""
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--broker":
            i++
            broker = args[i]
        case "--scenario":
            i++
            scenario = args[i]
        case "--output-atlas":
            i++
            atlasOut = args[i]
        case "--output-ledger":
            i++
            ledgerOut = args[i]
        default:
            return fmt.Errorf("unknown flag %s", args[i])
        }
    }
    if broker == "" || scenario == "" {
        return fmt.Errorf("--broker and --scenario required")
    }
    return mqttkernel.EmitSessionAtlas(broker, scenario, atlasOut, ledgerOut)
}

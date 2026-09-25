package main

import (
    "fmt"
    "os"

    "github.com/terminus/kcompactctl/internal/topicgate"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "pull-segments":
        err = runLoad(os.Args[2:])
    case "audit-log":
        err = runReconcile(os.Args[2:])
    case "publish-keys":
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
    fmt.Fprintln(os.Stderr, "kcompactctl pull-segments --topic TOPIC --scenario SCENARIO [--fixture-dir D]")
    fmt.Fprintln(os.Stderr, "kcompactctl audit-log --topic TOPIC --scenario SCENARIO")
    fmt.Fprintln(os.Stderr, "kcompactctl publish-keys --topic TOPIC --scenario SCENARIO [--output-snapshot PATH] [--output-lineage PATH]")
}

func runLoad(args []string) error {
    topic, scenario, fixtureDir := "", "", "/app/fixtures"
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--topic":
            i++
            topic = args[i]
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
    if topic == "" || scenario == "" {
        return fmt.Errorf("--topic and --scenario required")
    }
    snap, err := topicgate.MaterializeTopic(topic, scenario, fixtureDir)
    if err != nil {
        return err
    }
    return topicgate.PersistStaging(snap)
}

func runReconcile(args []string) error {
    topic, scenario := "", ""
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--topic":
            i++
            topic = args[i]
        case "--scenario":
            i++
            scenario = args[i]
        default:
            return fmt.Errorf("unknown flag %s", args[i])
        }
    }
    _ = topic
    if scenario == "" {
        return fmt.Errorf("--scenario required")
    }
    return topicgate.RunReconcilePass(topic, scenario)
}

func runEmit(args []string) error {
    topic, scenario := "", ""
    snapOut, linOut := "", ""
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--topic":
            i++
            topic = args[i]
        case "--scenario":
            i++
            scenario = args[i]
        case "--output-snapshot":
            i++
            snapOut = args[i]
        case "--output-lineage":
            i++
            linOut = args[i]
        default:
            return fmt.Errorf("unknown flag %s", args[i])
        }
    }
    if topic == "" || scenario == "" {
        return fmt.Errorf("--topic and --scenario required")
    }
    return topicgate.SealSnapshot(topic, scenario, snapOut, linOut)
}

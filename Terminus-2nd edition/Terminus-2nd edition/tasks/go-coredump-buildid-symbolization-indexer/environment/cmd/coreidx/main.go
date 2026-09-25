package main

import (
    "fmt"
    "os"

    "github.com/terminus/coreidx/internal/orchestrate"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "ingest":
        err = runIngest(os.Args[2:])
    case "export":
        err = runExport(os.Args[2:])
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
    fmt.Fprintln(os.Stderr, "coreidx ingest --crash-dir DIR --catalog PATH --staging PATH")
    fmt.Fprintln(os.Stderr, "coreidx export --staging PATH --sqlite PATH --summary PATH")
}

func runIngest(args []string) error {
    crashDir, catalog, staging := "", "", ""
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--crash-dir":
            i++
            crashDir = args[i]
        case "--catalog":
            i++
            catalog = args[i]
        case "--staging":
            i++
            staging = args[i]
        default:
            return fmt.Errorf("unknown flag %s", args[i])
        }
    }
    if crashDir == "" || catalog == "" || staging == "" {
        return fmt.Errorf("ingest requires --crash-dir, --catalog, --staging")
    }
    return orchestrate.RunIngest(crashDir, catalog, staging)
}

func runExport(args []string) error {
    staging, sqlitePath, summary := "", "", ""
    for i := 0; i < len(args); i++ {
        switch args[i] {
        case "--staging":
            i++
            staging = args[i]
        case "--sqlite":
            i++
            sqlitePath = args[i]
        case "--summary":
            i++
            summary = args[i]
        default:
            return fmt.Errorf("unknown flag %s", args[i])
        }
    }
    if staging == "" || sqlitePath == "" || summary == "" {
        return fmt.Errorf("export requires --staging, --sqlite, --summary")
    }
    return orchestrate.RunExport(staging, sqlitePath, summary)
}

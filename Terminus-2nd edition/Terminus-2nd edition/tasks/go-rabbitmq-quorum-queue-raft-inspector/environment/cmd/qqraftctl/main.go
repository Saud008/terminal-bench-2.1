package main

import (
    "fmt"
    "os"

    "github.com/terminus/qqraftctl/internal/runchain"
)

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(2)
    }
    var err error
    switch os.Args[1] {
    case "replay-log":
        err = runchain.ReplayLog(os.Args[2:])
    case "merge-snapshot":
        err = runchain.MergeSnapshot(os.Args[2:])
    case "audit-membership":
        err = runchain.AuditMembership(os.Args[2:])
    case "export-committed":
        err = runchain.ExportCommitted(os.Args[2:])
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
    fmt.Fprintln(os.Stderr, "qqraftctl replay-log --cluster C --scenario S [--fixture-dir D]")
    fmt.Fprintln(os.Stderr, "qqraftctl merge-snapshot --cluster C --scenario S [--fixture-dir D]")
    fmt.Fprintln(os.Stderr, "qqraftctl audit-membership --cluster C --scenario S")
    fmt.Fprintln(os.Stderr, "qqraftctl export-committed --cluster C --scenario S")
}

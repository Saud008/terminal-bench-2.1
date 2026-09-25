package main

import (
    "fmt"
    "os"

    "github.com/terminus/holdfairctl/internal/holdbridge"
)

func main() {
    if len(os.Args) < 2 {
        fmt.Fprintln(os.Stderr, "holdfairctl: missing subcommand")
        os.Exit(2)
    }
    if err := holdbridge.Dispatch(os.Args[1:]); err != nil {
        fmt.Fprintln(os.Stderr, err.Error())
        os.Exit(1)
    }
}

package main

import (
    "fmt"
    "os"

    "github.com/terminus/degaudit/internal/degbridge"
)

func main() {
    if len(os.Args) < 2 {
        fmt.Fprintln(os.Stderr, "degaudit: missing subcommand")
        os.Exit(2)
    }
    if err := degbridge.Dispatch(os.Args[1:]); err != nil {
        fmt.Fprintln(os.Stderr, err.Error())
        os.Exit(1)
    }
}

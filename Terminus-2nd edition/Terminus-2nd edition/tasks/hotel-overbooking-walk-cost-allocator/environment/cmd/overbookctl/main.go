package main

import (
    "fmt"
    "os"

    "github.com/terminus/overbookctl/internal/cmdsurface"
)

func main() {
    if len(os.Args) < 2 {
        fmt.Fprintln(os.Stderr, "overbookctl: missing subcommand")
        os.Exit(2)
    }
    if err := cmdsurface.Dispatch(os.Args[1:]); err != nil {
        fmt.Fprintln(os.Stderr, err.Error())
        os.Exit(1)
    }
}

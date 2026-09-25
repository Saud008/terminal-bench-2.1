package main

import (
    "fmt"
    "os"

    "github.com/terminus/venuetixctl/internal/ticketbridge"
)

func main() {
    if len(os.Args) < 2 {
        fmt.Fprintln(os.Stderr, "venuetixctl: missing subcommand")
        os.Exit(2)
    }
    if err := seatbridge.Dispatch(os.Args[1:]); err != nil {
        fmt.Fprintln(os.Stderr, err.Error())
        os.Exit(1)
    }
}

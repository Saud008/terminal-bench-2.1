package main

import (
    "fmt"
    "os"

    "github.com/terminus/gridplan/internal/gridrouter"
)

func main() {
    if len(os.Args) < 2 {
        fmt.Fprintln(os.Stderr, "gridplan: missing subcommand")
        os.Exit(2)
    }
    if err := gridrouter.Dispatch(os.Args[1:]); err != nil {
        fmt.Fprintln(os.Stderr, err.Error())
        os.Exit(1)
    }
}

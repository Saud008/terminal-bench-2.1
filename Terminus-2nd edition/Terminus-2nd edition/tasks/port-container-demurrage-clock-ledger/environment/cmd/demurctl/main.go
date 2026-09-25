package main

import (
	"fmt"
	"os"

	"github.com/terminus/demurctl/internal/yardbridge"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "demurctl: missing subcommand")
		os.Exit(2)
	}
	if err := yardbridge.Dispatch(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, err.Error())
		os.Exit(1)
	}
}

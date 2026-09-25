package main

import (
	"fmt"
	"os"

	"github.com/terminus/platclosectl/internal/orchestrate"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	verb := os.Args[1]
	scenario, out := "", ""
	args := os.Args[2:]
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--scenario":
			i++
			if i >= len(args) {
				usage()
				os.Exit(2)
			}
			scenario = args[i]
		case "--output":
			i++
			if i >= len(args) {
				usage()
				os.Exit(2)
			}
			out = args[i]
		default:
			fmt.Fprintf(os.Stderr, "unknown flag %s\n", args[i])
			usage()
			os.Exit(2)
		}
	}
	if scenario == "" {
		usage()
		os.Exit(2)
	}
	switch verb {
	case "hydrate-plates", "bind-residuals", "seal-closure":
		if err := orchestrate.Run(verb, scenario, out); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "platclosectl hydrate-plates --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "platclosectl bind-residuals --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "platclosectl seal-closure --scenario SCENARIO [--output PATH]")
}

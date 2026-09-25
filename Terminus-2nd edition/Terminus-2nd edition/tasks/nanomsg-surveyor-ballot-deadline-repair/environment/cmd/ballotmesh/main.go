package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/ballotmesh/internal/export"
	"github.com/terminus/ballotmesh/internal/mesh"
	"github.com/terminus/ballotmesh/internal/simulate"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "simulate":
		fs := flag.NewFlagSet("simulate", flag.ExitOnError)
		meshPath := fs.String("mesh", "", "mesh json path")
		output := fs.String("output", "/app/output/survey-report.json", "report path")
		_ = fs.Parse(os.Args[2:])
		if *meshPath == "" {
			fmt.Fprintln(os.Stderr, "missing --mesh")
			os.Exit(2)
		}
		m, err := mesh.Load(*meshPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "load mesh: %v\n", err)
			os.Exit(1)
		}
		if _, err := simulate.Run(m); err != nil {
			fmt.Fprintf(os.Stderr, "simulate: %v\n", err)
			os.Exit(1)
		}
		if err := export.WriteReport(*output, *meshPath); err != nil {
			fmt.Fprintf(os.Stderr, "export: %v\n", err)
			os.Exit(1)
		}
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: ballotmesh simulate --mesh PATH --output PATH")
}

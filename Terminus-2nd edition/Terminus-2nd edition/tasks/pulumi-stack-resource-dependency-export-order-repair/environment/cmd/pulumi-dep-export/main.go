package main

import (
	"fmt"
	"os"

	"github.com/terminus/pulumi-dep-export/internal/replay"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "order":
		if len(os.Args) != 6 || os.Args[2] != "--stack" || os.Args[4] != "--output" {
			usage()
			os.Exit(2)
		}
		os.Exit(replay.OrderStackCLI(os.Args[3], os.Args[5]))
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: pulumi-dep-export order --stack <snapshot.json> --output <report.json>")
}

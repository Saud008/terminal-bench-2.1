package main

import (
	"fmt"
	"os"

	"github.com/terminus/originctl/internal/classout"
	"github.com/terminus/originctl/internal/shipment"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "parse-shipment":
		err = runParse(os.Args[2:])
	case "score-origin":
		err = runScore(os.Args[2:])
	case "write-atlas":
		err = runWrite(os.Args[2:])
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
	fmt.Fprintln(os.Stderr, "originctl parse-shipment --manifest MANIFEST [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "originctl score-origin --manifest MANIFEST")
	fmt.Fprintln(os.Stderr, "originctl write-atlas --manifest MANIFEST [--output PATH]")
}

func runParse(args []string) error {
	manifest, fixtureDir := "", "/app/fixtures"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--manifest":
			i++
			manifest = args[i]
		case "--fixture-dir":
			i++
			fixtureDir = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if manifest == "" {
		return fmt.Errorf("--manifest required")
	}
	return shipment.ParseShipment(manifest, fixtureDir)
}

func runScore(args []string) error {
	manifest := ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--manifest":
			i++
			manifest = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if manifest == "" {
		return fmt.Errorf("--manifest required")
	}
	return classout.ScoreOrigin(manifest)
}

func runWrite(args []string) error {
	manifest, out := "", ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--manifest":
			i++
			manifest = args[i]
		case "--output":
			i++
			out = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if manifest == "" {
		return fmt.Errorf("--manifest required")
	}
	return classout.WriteAtlas(manifest, out)
}

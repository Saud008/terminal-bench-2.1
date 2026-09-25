package main

import (
	"fmt"
	"os"

	"github.com/terminus/bondacc/internal/pipeline"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "seed-schedules":
		err = pipeline.SeedSchedules(os.Args[2:])
	case "apply-trades":
		err = pipeline.ApplyTrades(os.Args[2:])
	case "run-accrual":
		err = pipeline.RunAccrual(os.Args[2:])
	case "publish-atlas":
		err = pipeline.PublishAtlas(os.Args[2:])
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
	fmt.Fprintln(os.Stderr, "bondacc seed-schedules --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "bondacc apply-trades --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "bondacc run-accrual --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "bondacc publish-atlas --scenario SCENARIO [--fixture-dir D]")
}

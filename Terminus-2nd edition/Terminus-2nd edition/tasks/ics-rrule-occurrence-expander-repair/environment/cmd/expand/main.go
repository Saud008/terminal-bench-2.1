package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/icalexpand/internal/pipeline"
)

func main() {
	ics := flag.String("ics", "", "path to calendar .ics")
	window := flag.String("window", "", "RFC3339 start/end interval")
	db := flag.String("db", "", "sqlite output path")
	flag.Parse()
	if *ics == "" || *window == "" || *db == "" {
		fmt.Fprintln(os.Stderr, "usage: expand --ics <path> --window <start>/<end> --db <path>")
		os.Exit(2)
	}
	if err := pipeline.Run(*ics, *window, *db); err != nil {
		fmt.Fprintln(os.Stderr, err.Error())
		os.Exit(1)
	}
}

package main

import (
	"fmt"
	"os"

	"nsecval/internal/validate"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "ingest":
		os.Exit(runIngest(os.Args[2:]))
	case "validate":
		os.Exit(runValidate(os.Args[2:]))
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: nsecval ingest --capture <path> --snapshot <path>")
	fmt.Fprintln(os.Stderr, "       nsecval validate --capture <path> --report <path> [--snapshot <path>]")
}

func runIngest(args []string) int {
	var capture, snapshot string
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--capture":
			i++
			capture = args[i]
		case "--snapshot":
			i++
			snapshot = args[i]
		}
	}
	if capture == "" || snapshot == "" {
		fmt.Fprintln(os.Stderr, "missing flags")
		return 2
	}
	if _, err := validate.IngestOnly(capture, snapshot); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	return 0
}

func runValidate(args []string) int {
	var capture, report, snapshot string
	snapshot = validate.DefaultSnapshotPath
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--capture":
			i++
			capture = args[i]
		case "--report":
			i++
			report = args[i]
		case "--snapshot":
			i++
			snapshot = args[i]
		}
	}
	if capture == "" || report == "" {
		fmt.Fprintln(os.Stderr, "missing flags")
		return 2
	}
	if _, err := validate.Run(capture, report, snapshot); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	return 0
}

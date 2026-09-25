package main

import (
	"fmt"
	"os"

	"github.com/terminus/vaultaud/internal/pipeline"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
    case "collect", "ingest", "audit":
        err = runCollect(os.Args[2:])
    case "publish", "export", "rollup":
        err = runPublish(os.Args[2:])
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
	fmt.Fprintln(os.Stderr, "vaultaud audit --transcript-dir DIR --config-dir DIR --staging PATH")
	fmt.Fprintln(os.Stderr, "vaultaud rollup --staging PATH --atlas PATH")
}

func runCollect(args []string) error {
	tdir, cdir, staging := "", "", ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--transcript-dir":
			i++
			tdir = args[i]
		case "--config-dir":
			i++
			cdir = args[i]
		case "--staging":
			i++
			staging = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if tdir == "" || cdir == "" || staging == "" {
		return fmt.Errorf("collect requires --transcript-dir, --config-dir, --staging")
	}
	return pipeline.RunCollect(tdir, cdir, staging)
}

func runPublish(args []string) error {
	staging, atlas := "", ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--staging":
			i++
			staging = args[i]
		case "--atlas":
			i++
			atlas = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if staging == "" || atlas == "" {
		return fmt.Errorf("publish requires --staging, --atlas")
	}
	return pipeline.RunPublish(staging, atlas)
}

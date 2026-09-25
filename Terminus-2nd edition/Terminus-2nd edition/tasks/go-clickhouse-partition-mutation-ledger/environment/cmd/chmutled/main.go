package main

import (
	"fmt"
	"os"

	"github.com/terminus/chmutled/internal/pipeline"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "reconcile-partitions":
		err = runReconcile(os.Args[2:])
	case "emit-readiness":
		err = runEmit(os.Args[2:])
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
	fmt.Fprintln(os.Stderr, "chmutled reconcile-partitions --metadata-dir DIR --mutations-dir DIR --replica-dir DIR --config-dir DIR --staging PATH")
	fmt.Fprintln(os.Stderr, "chmutled emit-readiness --staging PATH --sqlite PATH --atlas PATH")
}

func runReconcile(args []string) error {
	meta, mut, rep, cfg, staging := "", "", "", "", ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--metadata-dir":
			i++
			meta = args[i]
		case "--mutations-dir":
			i++
			mut = args[i]
		case "--replica-dir":
			i++
			rep = args[i]
		case "--config-dir":
			i++
			cfg = args[i]
		case "--staging":
			i++
			staging = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if meta == "" || mut == "" || rep == "" || cfg == "" || staging == "" {
		return fmt.Errorf("reconcile-partitions requires all directory flags and --staging")
	}
	return pipeline.RunReconcile(meta, mut, rep, cfg, staging)
}

func runEmit(args []string) error {
	staging, sqlitePath, atlas := "", "", ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--staging":
			i++
			staging = args[i]
		case "--sqlite":
			i++
			sqlitePath = args[i]
		case "--atlas":
			i++
			atlas = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if staging == "" || sqlitePath == "" || atlas == "" {
		return fmt.Errorf("emit-readiness requires --staging, --sqlite, --atlas")
	}
	return pipeline.RunEmit(staging, sqlitePath, atlas)
}

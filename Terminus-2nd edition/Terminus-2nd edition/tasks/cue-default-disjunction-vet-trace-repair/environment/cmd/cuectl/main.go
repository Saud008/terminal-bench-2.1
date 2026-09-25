package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/cuectl/internal/cuewrap"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "vet":
		runVet(os.Args[2:])
	case "export":
		runExport(os.Args[2:])
	default:
		usage()
		os.Exit(2)
	}
}

func runVet(args []string) {
	fs := flag.NewFlagSet("vet", flag.ExitOnError)
	workspace := fs.String("workspace", "", "workspace directory")
	seed := fs.String("seed", "", "seed")
	export := fs.String("export", "", "output json path")
	_ = fs.Parse(args)
	if *workspace == "" || *seed == "" || *export == "" {
		usage()
		os.Exit(2)
	}
	doc, err := cuewrap.RunVet(*workspace, *seed)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	data, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := os.WriteFile(*export, data, 0o644); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if !doc.OK {
		os.Exit(1)
	}
}

func runExport(args []string) {
	fs := flag.NewFlagSet("export", flag.ExitOnError)
	workspace := fs.String("workspace", "", "workspace directory")
	seed := fs.String("seed", "", "seed")
	export := fs.String("export", "", "output json path")
	_ = fs.Parse(args)
	if *workspace == "" || *seed == "" || *export == "" {
		usage()
		os.Exit(2)
	}
	doc, err := cuewrap.RunExport(*workspace, *seed)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	data, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := os.WriteFile(*export, data, 0o644); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func usage() {
	fmt.Fprintf(os.Stderr, "usage: %s vet|export --workspace <dir> --seed <seed> --export <json>\n", filepath.Base(os.Args[0]))
}

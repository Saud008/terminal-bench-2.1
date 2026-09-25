package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"

	"github.com/terminus/bundlectl/internal/eval"
	"github.com/terminus/bundlectl/internal/verify"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: bundlectl <verify|eval> ...")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "verify":
		runVerify(os.Args[2:])
	case "eval":
		runEval(os.Args[2:])
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
}

func runVerify(args []string) {
	if len(args) > 0 {
		for _, a := range args {
			if a == "--seed" || strings.HasPrefix(a, "--seed=") {
				fmt.Fprintln(os.Stderr, "verify does not accept --seed")
				os.Exit(2)
			}
		}
	}
	fs := flag.NewFlagSet("verify", flag.ExitOnError)
	bundle := fs.String("bundle", "", "bundle directory")
	_ = fs.Parse(args)
	if *bundle == "" {
		fmt.Fprintln(os.Stderr, "--bundle required")
		os.Exit(2)
	}
	res, err := verify.Run(*bundle)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	_ = enc.Encode(res)
	if !res.OK {
		os.Exit(1)
	}
}

func runEval(args []string) {
	fs := flag.NewFlagSet("eval", flag.ExitOnError)
	bundle := fs.String("bundle", "", "bundle directory")
	seed := fs.String("seed", "", "seed")
	input := fs.String("input", "", "input json")
	export := fs.String("export", "", "export path")
	_ = fs.Parse(args)
	if *bundle == "" || *seed == "" || *input == "" {
		fmt.Fprintln(os.Stderr, "--bundle --seed --input required")
		os.Exit(2)
	}
	res, err := eval.Run(*bundle, *seed, *input)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if *export != "" {
		f, err := os.Create(*export)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		enc := json.NewEncoder(f)
		enc.SetIndent("", "  ")
		_ = enc.Encode(res)
		_ = f.Close()
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	_ = enc.Encode(res)
}

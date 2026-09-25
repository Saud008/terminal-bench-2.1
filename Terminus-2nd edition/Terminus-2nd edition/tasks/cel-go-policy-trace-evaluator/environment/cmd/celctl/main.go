package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"celctl/internal/ingest"
	"celctl/internal/staging"
	"celctl/internal/trace"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "ingest":
		runIngest(os.Args[2:])
	case "eval":
		runEval(os.Args[2:])
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: celctl ingest --input PATH --staging PATH")
	fmt.Fprintln(os.Stderr, "       celctl eval --staging PATH --env PATH [--result-out PATH] [--trace] [--trace-out PATH]")
}

func runIngest(args []string) {
	fs := flag.NewFlagSet("ingest", flag.ExitOnError)
	in := fs.String("input", "", "input AST JSON")
	out := fs.String("staging", "/app/state/cel-staging.json", "staging output")
	_ = fs.Parse(args)
	if *in == "" {
		fmt.Fprintln(os.Stderr, "ingest: --input required")
		os.Exit(2)
	}
	file, err := ingest.LoadInput(*in)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := staging.WriteSnapshot(*in, file, *out); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func runEval(args []string) {
	fs := flag.NewFlagSet("eval", flag.ExitOnError)
	stagingPath := fs.String("staging", "", "staging snapshot")
	envPath := fs.String("env", "", "environment JSON")
	resultOut := fs.String("result-out", "", "result JSON path")
	doTrace := fs.Bool("trace", false, "write trace")
	traceOut := fs.String("trace-out", "/app/output/trace.json", "trace JSON path")
	_ = fs.Parse(args)
	if *stagingPath == "" || *envPath == "" {
		fmt.Fprintln(os.Stderr, "eval: --staging and --env required")
		os.Exit(2)
	}
	env, err := loadEnv(*envPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	tout := ""
	if *doTrace {
		tout = *traceOut
	}
	if err := trace.ExportEval(*stagingPath, env, *resultOut, tout); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func loadEnv(path string) (map[string]any, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var env map[string]any
	if err := json.Unmarshal(raw, &env); err != nil {
		return nil, err
	}
	return env, nil
}

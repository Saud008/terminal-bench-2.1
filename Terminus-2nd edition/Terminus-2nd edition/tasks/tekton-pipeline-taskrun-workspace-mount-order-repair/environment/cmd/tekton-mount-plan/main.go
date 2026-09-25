package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"github.com/terminus/tekton-mount-plan/internal/bind"
	"github.com/terminus/tekton-mount-plan/internal/parse"
	"github.com/terminus/tekton-mount-plan/internal/plan"
)

func main() {
	os.Exit(run(os.Args[1:]))
}

func run(args []string) int {
	if len(args) < 1 {
		printUsage()
		return 2
	}
	switch args[0] {
	case "parse":
		return runParse(args[1:])
	case "bind":
		return runBind(args[1:])
	case "plan":
		return runPlan(args[1:])
	default:
		printUsage()
		return 2
	}
}

func runParse(args []string) int {
	fs := flag.NewFlagSet("parse", flag.ContinueOnError)
	file := fs.String("file", "", "PipelineRun YAML path")
	if fs.Parse(args) != nil || *file == "" {
		printUsage()
		return 2
	}
	out, err := parse.LoadFile(*file)
	if err != nil {
		fmt.Fprintf(os.Stderr, "parse error: %v\n", err)
		return 1
	}
	return emit(out)
}

func runBind(args []string) int {
	fs := flag.NewFlagSet("bind", flag.ContinueOnError)
	file := fs.String("file", "", "PipelineRun YAML path")
	if fs.Parse(args) != nil || *file == "" {
		printUsage()
		return 2
	}
	out, err := bind.BindFile(*file)
	if err != nil {
		fmt.Fprintf(os.Stderr, "bind error: %v\n", err)
		return 1
	}
	return emit(out)
}

func runPlan(args []string) int {
	fs := flag.NewFlagSet("plan", flag.ContinueOnError)
	file := fs.String("file", "", "PipelineRun YAML path")
	if fs.Parse(args) != nil || *file == "" {
		printUsage()
		return 2
	}
	out, err := plan.PlanFile(*file)
	if err != nil {
		fmt.Fprintf(os.Stderr, "plan error: %v\n", err)
		return 1
	}
	return emit(out)
}

func emit(v any) int {
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(v); err != nil {
		fmt.Fprintf(os.Stderr, "encode error: %v\n", err)
		return 1
	}
	return 0
}

func printUsage() {
	fmt.Fprintln(os.Stderr, "usage: tekton-mount-plan <parse|bind|plan> --file <path>")
}

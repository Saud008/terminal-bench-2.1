package main

import (
	"flag"
	"fmt"
	"os"
	"strconv"

	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/model"
	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/scan"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: parquet-pushdown-scan filter --catalog <path> --output <path> [--is-null col] [--ts-gte ts] [--workers n]")
		os.Exit(2)
	}
	if os.Args[1] != "filter" {
		fmt.Fprintf(os.Stderr, "unknown command: %s\n", os.Args[1])
		os.Exit(2)
	}
	fs := flag.NewFlagSet("filter", flag.ExitOnError)
	catalog := fs.String("catalog", "", "catalog json path")
	output := fs.String("output", "", "filter output json path")
	isNull := fs.String("is-null", "", "column for IS NULL predicate")
	tsGte := fs.String("ts-gte", "", "measured_at lower bound (RFC3339 Z)")
	workers := fs.String("workers", "1", "parallel worker count")
	_ = fs.Parse(os.Args[2:])
	if *catalog == "" || *output == "" {
		fmt.Fprintln(os.Stderr, "filter requires --catalog and --output")
		os.Exit(2)
	}
	w, err := strconv.Atoi(*workers)
	if err != nil || w < 1 {
		fmt.Fprintln(os.Stderr, "invalid --workers")
		os.Exit(2)
	}
	spec := model.FilterSpec{
		IsNullCol: *isNull,
		TsGte:     *tsGte,
		Workers:   w,
	}
	os.Exit(scan.FilterCLI(*catalog, *output, spec))
}

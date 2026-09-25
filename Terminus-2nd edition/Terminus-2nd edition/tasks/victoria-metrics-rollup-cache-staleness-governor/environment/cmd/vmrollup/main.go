package main

import (
	"fmt"
	"os"

	"github.com/chronostack/metricrollup/internal/query"
	"github.com/chronostack/metricrollup/internal/scrape"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "ingest":
		if err := runIngest(os.Args[2:]); err != nil {
			fmt.Fprintf(os.Stderr, "ingest: %v\n", err)
			os.Exit(1)
		}
	case "query":
		if err := runQuery(os.Args[2:]); err != nil {
			fmt.Fprintf(os.Stderr, "query: %v\n", err)
			os.Exit(1)
		}
	default:
		usage()
		os.Exit(2)
	}
}

func runIngest(args []string) error {
	scrapeDir := ""
	cfgPath := "/app/config/rollup.json"
	dbPath := "/app/data/metrics.db"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--scrape-dir":
			i++
			if i >= len(args) {
				return os.ErrInvalid
			}
			scrapeDir = args[i]
		case "--config":
			i++
			cfgPath = args[i]
		case "--db":
			i++
			dbPath = args[i]
		}
	}
	if scrapeDir == "" {
		return os.ErrInvalid
	}
	return scrape.Ingest(scrapeDir, cfgPath, dbPath)
}

func runQuery(args []string) error {
	metric := ""
	var windowStartMs, windowEndMs, queryMs int64
	cfgPath := "/app/config/rollup.json"
	dbPath := "/app/data/metrics.db"
	output := "/app/output/query-report.json"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--metric":
			i++
			metric = args[i]
		case "--window-start-ms":
			i++
			fmt.Sscan(args[i], &windowStartMs)
		case "--window-end-ms":
			i++
			fmt.Sscan(args[i], &windowEndMs)
		case "--config":
			i++
			cfgPath = args[i]
		case "--db":
			i++
			dbPath = args[i]
		case "--output":
			i++
			output = args[i]
		case "--query-ms":
			i++
			var q int64
			fmt.Sscan(args[i], &q)
			queryMs = q
		}
	}
	return query.Run(metric, windowStartMs, windowEndMs, cfgPath, dbPath, output, queryMs)
}

func usage() {
	fmt.Fprintf(os.Stderr, "usage: vmrollup ingest|query [flags]\n")
}

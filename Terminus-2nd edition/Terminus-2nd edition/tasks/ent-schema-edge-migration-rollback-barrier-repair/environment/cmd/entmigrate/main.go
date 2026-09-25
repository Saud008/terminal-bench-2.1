package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"github.com/terminus/ent-migrate/internal/db"
	"github.com/terminus/ent-migrate/internal/migrate"
	"github.com/terminus/ent-migrate/internal/model"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: entmigrate up|down")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "up":
		runUp(os.Args[2:])
	case "down":
		runDown(os.Args[2:])
	default:
		fmt.Fprintf(os.Stderr, "unknown command %q\n", os.Args[1])
		os.Exit(2)
	}
}

func runUp(args []string) {
	fs := flag.NewFlagSet("up", flag.ExitOnError)
	catalogPath := fs.String("catalog", "/app/fixtures/catalogs/bundled-v3.json", "migration catalog")
	dbPath := fs.String("db", "/app/work/test.db", "sqlite database path")
	seed := fs.String("seed", "bundled", "fixture seed name")
	reportPath := fs.String("report", "/app/output/migration-report.json", "report output")
	_ = fs.Parse(args)

	cat, err := model.LoadCatalog(*catalogPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "catalog: %v\n", err)
		os.Exit(1)
	}
	conn, err := db.Open(*dbPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "db: %v\n", err)
		os.Exit(1)
	}
	defer conn.Close()

	if err := db.ApplySeed(conn, *seed); err != nil {
		fmt.Fprintf(os.Stderr, "seed: %v\n", err)
		os.Exit(1)
	}

	report, err := migrate.RunUp(conn, cat)
	if err != nil {
		fmt.Fprintf(os.Stderr, "migrate up: %v\n", err)
		os.Exit(1)
	}
	report.Seed = *seed
	if err := writeReport(*reportPath, report); err != nil {
		fmt.Fprintf(os.Stderr, "report: %v\n", err)
		os.Exit(1)
	}
}

func runDown(args []string) {
	fs := flag.NewFlagSet("down", flag.ExitOnError)
	catalogPath := fs.String("catalog", "/app/fixtures/catalogs/bundled-v3.json", "migration catalog")
	dbPath := fs.String("db", "/app/work/test.db", "sqlite database path")
	steps := fs.Int("steps", 1, "down steps to apply")
	reportPath := fs.String("report", "/app/output/migration-report.json", "report output")
	_ = fs.Parse(args)

	cat, err := model.LoadCatalog(*catalogPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "catalog: %v\n", err)
		os.Exit(1)
	}
	conn, err := db.Open(*dbPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "db: %v\n", err)
		os.Exit(1)
	}
	defer conn.Close()

	report, err := migrate.RunDown(conn, cat, *steps)
	if err != nil {
		fmt.Fprintf(os.Stderr, "migrate down: %v\n", err)
		os.Exit(1)
	}
	if err := writeReport(*reportPath, report); err != nil {
		fmt.Fprintf(os.Stderr, "report: %v\n", err)
		os.Exit(1)
	}
}

func writeReport(path string, report *model.Report) error {
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}

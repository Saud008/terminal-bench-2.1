package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/packstate"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/config"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/emittalerts"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/packload"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/runscan"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	cfg, err := config.Load("/app/config/dbtsent.json")
	if err != nil {
		fail(err)
	}
	switch os.Args[1] {
	case "ingest":
		runIngest(cfg)
	case "evaluate":
		if len(os.Args) >= 3 && os.Args[2] == "scan" {
			runEvaluate(cfg)
		} else {
			usage()
			os.Exit(2)
		}
	case "export":
		if len(os.Args) >= 3 && os.Args[2] == "alerts" {
			runExport(cfg)
		} else {
			usage()
			os.Exit(2)
		}
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: dbtsent ingest|evaluate scan|export alerts ...")
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}

func fixtureDir(cfg model.Config) string {
	if d := os.Getenv("TB3_BUNDLE_DIR"); d != "" {
		return d
	}
	return cfg.BundleDir
}

func runIngest(cfg model.Config) {
	fs := flag.NewFlagSet("ingest", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	bundle := fs.String("bundle", "", "bundle")
	_ = fs.Parse(os.Args[2:])
	if *seed == "" || *bundle == "" {
		fail(fmt.Errorf("seed and bundle required"))
	}
	dir := fixtureDir(cfg)
	raw, err := packload.LoadBundle(dir, *bundle, *seed)
	if err != nil {
		fail(err)
	}
	if err := packstate.WriteSnapshot(cfg.StagingPath, *seed, *bundle, raw); err != nil {
		fail(err)
	}
}

func runEvaluate(cfg model.Config) {
	fs := flag.NewFlagSet("evaluate", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	bundle := fs.String("bundle", "", "bundle")
	_ = fs.Parse(os.Args[3:])
	if *seed == "" || *bundle == "" {
		fail(fmt.Errorf("seed and bundle required"))
	}
	if _, err := runscan.RunScan(runscan.Input{
		Seed:        *seed,
		Pack:        *bundle,
		StagingPath: cfg.StagingPath,
		DBPath:      cfg.SentinelDBPath,
	}); err != nil {
		fail(err)
	}
}

func runExport(cfg model.Config) {
	fs := flag.NewFlagSet("export", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	bundle := fs.String("bundle", "", "bundle")
	out := fs.String("output", "", "output path")
	_ = fs.Parse(os.Args[3:])
	if *seed == "" || *bundle == "" || *out == "" {
		fail(fmt.Errorf("seed, bundle, output required"))
	}
	rep, err := emittalerts.BuildReport(cfg.StagingPath, cfg.SentinelDBPath, *seed, *bundle)
	if err != nil {
		fail(err)
	}
	if err := emittalerts.WriteReport(*out, rep); err != nil {
		fail(err)
	}
}

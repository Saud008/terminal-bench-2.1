// mlprov experiment provenance closure kernels — numerical workflow in /app/docs/scientific-computing-workflow.md
package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/mlflow-provenance-curator/internal/config"
	"github.com/terminus/mlflow-provenance-curator/internal/curate"
	"github.com/terminus/mlflow-provenance-curator/internal/export"
	"github.com/terminus/mlflow-provenance-curator/internal/ingest"
	"github.com/terminus/mlflow-provenance-curator/internal/model"
	"github.com/terminus/mlflow-provenance-curator/internal/staging"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	cfg, err := config.Load("/app/config/mlprov.json")
	if err != nil {
		fail(err)
	}
	switch os.Args[1] {
	case "ingest":
		runIngest(cfg)
	case "curate":
		if len(os.Args) >= 3 && os.Args[2] == "bind" {
			runCurate(cfg)
		} else {
			usage()
			os.Exit(2)
		}
	case "export":
		if len(os.Args) >= 3 && os.Args[2] == "summary" {
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
	fmt.Fprintln(os.Stderr, "usage: mlprov ingest|curate bind|export summary ...")
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}

func fixtureDir(cfg model.Config) string {
	if d := os.Getenv("TB3_FIXTURE_DIR"); d != "" {
		return d
	}
	return cfg.ScenarioDir
}

func runIngest(cfg model.Config) {
	fs := flag.NewFlagSet("ingest", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	scenario := fs.String("scenario", "", "scenario")
	_ = fs.Parse(os.Args[2:])
	if *seed == "" || *scenario == "" {
		fail(fmt.Errorf("seed and scenario required"))
	}
	path := ingest.ScenarioPath(fixtureDir(cfg), *scenario)
	sc, err := ingest.LoadScenario(path, *seed)
	if err != nil {
		fail(err)
	}
	if err := staging.WriteSnapshot(cfg.StagingPath, *seed, *scenario, sc); err != nil {
		fail(err)
	}
}

func runCurate(cfg model.Config) {
	fs := flag.NewFlagSet("curate", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	scenario := fs.String("scenario", "", "scenario")
	_ = fs.Parse(os.Args[3:])
	if *seed == "" || *scenario == "" {
		fail(fmt.Errorf("seed and scenario required"))
	}
	if _, err := curate.RunBind(curate.Input{
		Seed: *seed, Scenario: *scenario,
		StagingPath: cfg.StagingPath, DBPath: cfg.ProvenanceDBPath,
	}); err != nil {
		fail(err)
	}
}

func runExport(cfg model.Config) {
	fs := flag.NewFlagSet("export", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	scenario := fs.String("scenario", "", "scenario")
	out := fs.String("output", "", "output path")
	_ = fs.Parse(os.Args[3:])
	if *seed == "" || *scenario == "" || *out == "" {
		fail(fmt.Errorf("seed, scenario, output required"))
	}
	rep, err := export.BuildReport(cfg.StagingPath, cfg.ProvenanceDBPath, *seed, *scenario)
	if err != nil {
		fail(err)
	}
	if err := export.WriteReport(*out, rep); err != nil {
		fail(err)
	}
}

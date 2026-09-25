package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/feast-pit-join/internal/model"
	"github.com/terminus/feast-pit-join/internal/config"
	"github.com/terminus/feast-pit-join/internal/export"
	"github.com/terminus/feast-pit-join/internal/ingest"
	"github.com/terminus/feast-pit-join/internal/staging"
	"github.com/terminus/feast-pit-join/internal/validate"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	cfg, err := config.Load("/app/config/feastctl.json")
	if err != nil {
		fail(err)
	}
	switch os.Args[1] {
	case "load":
		runLoad(cfg)
	case "validate":
		if len(os.Args) >= 3 && os.Args[2] == "join" {
			runValidate(cfg)
		} else {
			usage()
			os.Exit(2)
		}
	case "export":
		if len(os.Args) >= 3 && os.Args[2] == "report" {
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
	fmt.Fprintln(os.Stderr, "usage: feastctl load|validate join|export report ...")
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

func runLoad(cfg model.Config) {
	fs := flag.NewFlagSet("load", flag.ExitOnError)
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

func runValidate(cfg model.Config) {
	fs := flag.NewFlagSet("validate", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	scenario := fs.String("scenario", "", "scenario")
	_ = fs.Parse(os.Args[3:])
	if *seed == "" || *scenario == "" {
		fail(fmt.Errorf("seed and scenario required"))
	}
	if err := validate.RunJoin(validate.Input{
		Seed: *seed, Scenario: *scenario,
		StagingPath: cfg.StagingPath, DBPath: cfg.ParityDBPath,
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
	rep, err := export.BuildReport(cfg.StagingPath, cfg.ParityDBPath, *seed, *scenario)
	if err != nil {
		fail(err)
	}
	if err := export.WriteReport(*out, rep); err != nil {
		fail(err)
	}
}

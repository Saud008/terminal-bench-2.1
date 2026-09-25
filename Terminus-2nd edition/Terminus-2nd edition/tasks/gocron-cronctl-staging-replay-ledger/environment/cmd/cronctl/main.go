package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/gocron-overlap-repair/internal/config"
	"github.com/terminus/gocron-overlap-repair/internal/ingest"
	"github.com/terminus/gocron-overlap-repair/internal/ledger"
	"github.com/terminus/gocron-overlap-repair/internal/model"
	"github.com/terminus/gocron-overlap-repair/internal/replay"
	"github.com/terminus/gocron-overlap-repair/internal/staging"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: cronctl <load|replay|export> ...")
		os.Exit(2)
	}
	cfgPath := "/app/config/scheduler.json"
	cfg, err := config.Load(cfgPath)
	if err != nil {
		fail(err)
	}
	switch os.Args[1] {
	case "load":
		runLoad(cfg)
	case "replay":
		runReplay(cfg)
	case "export":
		runExport(cfg)
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}

func fixtureDir() string {
	if d := os.Getenv("TB3_FIXTURE_DIR"); d != "" {
		return d
	}
	return "/app/fixtures/scenarios"
}

func runLoad(cfg model.Config) {
	fs := flag.NewFlagSet("load", flag.ExitOnError)
	seed := fs.String("seed", "", "seed namespace")
	scenario := fs.String("scenario", "", "scenario name")
	_ = fs.Parse(os.Args[2:])
	if *seed == "" || *scenario == "" {
		fail(fmt.Errorf("seed and scenario required"))
	}
	path := ingest.ScenarioPath(fixtureDir(), *scenario)
	sc, err := ingest.LoadScenario(path, *seed)
	if err != nil {
		fail(err)
	}
	if err := staging.WriteSnapshot(cfg.StagingPath, *seed, *scenario, sc, cfg.DefaultLocation); err != nil {
		fail(err)
	}
}

func runReplay(cfg model.Config) {
	fs := flag.NewFlagSet("replay", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	scenario := fs.String("scenario", "", "scenario")
	_ = fs.Parse(os.Args[2:])
	if *seed == "" || *scenario == "" {
		fail(fmt.Errorf("seed and scenario required"))
	}
	path := ingest.ScenarioPath(fixtureDir(), *scenario)
	sc, err := ingest.LoadScenario(path, *seed)
	if err != nil {
		fail(err)
	}
	store, err := ledger.Open(cfg.LedgerPath)
	if err != nil {
		fail(err)
	}
	defer store.Close()
	if err := store.Reset(); err != nil {
		fail(err)
	}
	if err := replay.Run(replay.RunInput{
		Seed: *seed, ScenarioName: *scenario, StagingPath: cfg.StagingPath,
		Scenario: sc, Cfg: cfg, Store: store,
	}); err != nil {
		fail(err)
	}
}

func runExport(cfg model.Config) {
	fs := flag.NewFlagSet("export", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	scenario := fs.String("scenario", "", "scenario")
	out := fs.String("output", "", "output path")
	_ = fs.Parse(os.Args[2:])
	if *seed == "" || *scenario == "" || *out == "" {
		fail(fmt.Errorf("seed, scenario, output required"))
	}
	store, err := ledger.Open(cfg.LedgerPath)
	if err != nil {
		fail(err)
	}
	defer store.Close()
	exp, err := replay.BuildLedgerExport(store, cfg.StagingPath, *seed, *scenario)
	if err != nil {
		fail(err)
	}
	if err := replay.WriteLedgerExport(*out, exp); err != nil {
		fail(err)
	}
	_ = filepath.Dir(*out)
}

package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/bundleloader"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/buffer"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/compiler"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/config"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/publisher"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	cfg, err := config.Load("/app/config/nomrep.json")
	if err != nil {
		fail(err)
	}
	switch os.Args[1] {
	case "load", "ingest":
		runLoad(cfg)
	case "compile", "index":
		runCompile(cfg)
	case "publish", "export":
		runPublish(cfg)
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: nomrep load|compile|publish ...")
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
	path := bundleloader.ScenarioPath(fixtureDir(cfg), *scenario)
	sc, err := bundleloader.LoadScenario(path, *seed)
	if err != nil {
		fail(err)
	}
	if err := buffer.WriteSnapshot(cfg.BufferPath, *seed, *scenario, sc); err != nil {
		fail(err)
	}
}

func runCompile(cfg model.Config) {
	fs := flag.NewFlagSet("compile", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	scenario := fs.String("scenario", "", "scenario")
	_ = fs.Parse(os.Args[2:])
	if *seed == "" || *scenario == "" {
		fail(fmt.Errorf("seed and scenario required"))
	}
	if _, err := compiler.RunCompile(compiler.Input{
		Seed: *seed, Scenario: *scenario,
		BufferPath: cfg.BufferPath, DBPath: cfg.AtlasDBPath,
	}); err != nil {
		fail(err)
	}
}

func runPublish(cfg model.Config) {
	fs := flag.NewFlagSet("publish", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	scenario := fs.String("scenario", "", "scenario")
	out := fs.String("output", "", "output path")
	_ = fs.Parse(os.Args[2:])
	if *seed == "" || *scenario == "" || *out == "" {
		fail(fmt.Errorf("seed, scenario, output required"))
	}
	rep, err := publisher.BuildAtlas(cfg.BufferPath, cfg.AtlasDBPath, *seed, *scenario)
	if err != nil {
		fail(err)
	}
	if err := publisher.WriteAtlas(*out, rep); err != nil {
		fail(err)
	}
}

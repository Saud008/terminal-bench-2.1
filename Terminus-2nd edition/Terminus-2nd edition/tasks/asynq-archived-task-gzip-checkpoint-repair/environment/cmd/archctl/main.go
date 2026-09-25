package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/asynq-archive-repair/internal/archive"
	"github.com/terminus/asynq-archive-repair/internal/config"
	"github.com/terminus/asynq-archive-repair/internal/export"
	"github.com/terminus/asynq-archive-repair/internal/ingest"
	"github.com/terminus/asynq-archive-repair/internal/model"
	"github.com/terminus/asynq-archive-repair/internal/queue"
	"github.com/terminus/asynq-archive-repair/internal/restore"
	"github.com/terminus/asynq-archive-repair/internal/retention"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: archctl <seed|archive|restore|purge|manifest> ...")
		os.Exit(2)
	}
	cfgPath := "/app/config/queue.json"
	args := os.Args[2:]
	for i := 0; i < len(args)-1; i++ {
		if args[i] == "--config" {
			cfgPath = args[i+1]
		}
	}
	cfg, err := config.Load(cfgPath)
	if err != nil {
		fail(err)
	}
	store, err := queue.Open(cfg.QueuePath)
	if err != nil {
		fail(err)
	}
	defer store.Close()

	switch os.Args[1] {
	case "seed":
		runSeed(store, cfg)
	case "archive":
		runArchive(store, cfg)
	case "restore":
		runRestore(store, cfg)
	case "purge":
		runPurge(store, cfg)
	case "manifest":
		runManifest(store, cfg)
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}

func runSeed(store *queue.Store, cfg model.Config) {
	fs := flag.NewFlagSet("seed", flag.ExitOnError)
	seed := fs.String("seed", "", "seed namespace")
	scenario := fs.String("scenario", "", "scenario name")
	_ = fs.Parse(os.Args[2:])
	if *seed == "" || *scenario == "" {
		fail(fmt.Errorf("seed and scenario required"))
	}
	path := filepath.Join("/app/fixtures/scenarios", *scenario+".jsonl")
	tasks, err := ingest.LoadScenario(path, *seed, cfg.DefaultQueue)
	if err != nil {
		fail(err)
	}
	if err := store.Reset(); err != nil {
		fail(err)
	}
	if err := ingest.SeedQueue(store, tasks); err != nil {
		fail(err)
	}
}

func runArchive(store *queue.Store, cfg model.Config) {
	fs := flag.NewFlagSet("archive", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	scenario := fs.String("scenario", "", "scenario")
	_ = fs.Parse(os.Args[2:])
	if *seed == "" || *scenario == "" {
		fail(fmt.Errorf("seed and scenario required"))
	}
	partial := *scenario == "partial-member"
	if err := archive.RunArchive(store, archive.RunInput{
		Seed: *seed, Scenario: *scenario, Cfg: cfg, Partial: partial,
	}); err != nil {
		fail(err)
	}
}

func runRestore(store *queue.Store, cfg model.Config) {
	fs := flag.NewFlagSet("restore", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	scenario := fs.String("scenario", "", "scenario")
	_ = fs.Parse(os.Args[2:])
	if *seed == "" || *scenario == "" {
		fail(fmt.Errorf("seed and scenario required"))
	}
	base := filepath.Join(cfg.ArchiveDir, fmt.Sprintf("%s-%s", *seed, *scenario))
	idx, err := archive.ReadIndex(base + ".idx.json")
	if err != nil {
		fail(err)
	}
	if err := restore.ImportBundle(store, base+".bundle", idx); err != nil {
		fail(err)
	}
}

func runPurge(store *queue.Store, cfg model.Config) {
	fs := flag.NewFlagSet("purge", flag.ExitOnError)
	before := fs.String("before", "", "RFC3339 cutoff")
	_ = fs.Parse(os.Args[2:])
	if *before == "" {
		fail(fmt.Errorf("--before required"))
	}
	if _, err := retention.PurgeBefore(store, *before, cfg.RetentionSkewMs); err != nil {
		fail(err)
	}
}

func runManifest(store *queue.Store, cfg model.Config) {
	fs := flag.NewFlagSet("manifest", flag.ExitOnError)
	seed := fs.String("seed", "", "seed")
	scenario := fs.String("scenario", "", "scenario")
	out := fs.String("output", "", "output path")
	_ = fs.Parse(os.Args[2:])
	if *seed == "" || *scenario == "" || *out == "" {
		fail(fmt.Errorf("seed, scenario, output required"))
	}
	m, err := export.BuildManifest(store, cfg.StagingPath, *seed, *scenario)
	if err != nil {
		fail(err)
	}
	if err := export.WriteManifest(*out, m); err != nil {
		fail(err)
	}
}

package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/modbus-drift-cataloger/internal/catalog"
	"github.com/terminus/modbus-drift-cataloger/internal/config"
	"github.com/terminus/modbus-drift-cataloger/internal/export"
	"github.com/terminus/modbus-drift-cataloger/internal/ingest"
	"github.com/terminus/modbus-drift-cataloger/internal/manifest"
	"github.com/terminus/modbus-drift-cataloger/internal/model"
	"github.com/terminus/modbus-drift-cataloger/internal/staging"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: modbusctl <ingest|catalog|export|run> ...")
		os.Exit(2)
	}
	cfg, err := config.Load("/app/config/catalog.json")
	if err != nil {
		fail(err)
	}
	switch os.Args[1] {
	case "ingest":
		runIngest(cfg)
	case "catalog":
		runCatalog(cfg)
	case "export":
		runExport(cfg)
	case "run":
		runAll(cfg)
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}

func fixtureRoot() string {
	if d := os.Getenv("TB3_FIXTURE_DIR"); d != "" {
		return d
	}
	return "/app/fixtures"
}

func runIngest(cfg model.Config) {
	fs := flag.NewFlagSet("ingest", flag.ExitOnError)
	manifestPath := fs.String("manifest", "", "device manifest json")
	framesPath := fs.String("frames", "", "poll frames jsonl")
	_ = fs.Parse(os.Args[2:])
	if *manifestPath == "" || *framesPath == "" {
		fail(fmt.Errorf("manifest and frames required"))
	}
	frames, err := ingest.LoadFrames(*framesPath)
	if err != nil {
		fail(err)
	}
	if err := ingest.WriteStaging(cfg.StagingPath, cfg.StagingSeqPath, *manifestPath, frames); err != nil {
		fail(err)
	}
}

func runCatalog(cfg model.Config) {
	snap, err := staging.Read(cfg.StagingPath)
	if err != nil {
		fail(err)
	}
	mpath, err := resolveManifest(snap)
	if err != nil {
		fail(err)
	}
	m, err := manifest.Load(mpath)
	if err != nil {
		fail(err)
	}
	if err := catalog.RunCatalog(m, snap, cfg.CatalogGenerationPath, cfg.RejectedFramesPath); err != nil {
		fail(err)
	}
}

func runExport(cfg model.Config) {
	snap, err := staging.Read(cfg.StagingPath)
	if err != nil {
		fail(err)
	}
	if err := export.RunExport(snap, cfg.CatalogGenerationPath, cfg.DriftCatalogPath); err != nil {
		fail(err)
	}
}

func runAll(cfg model.Config) {
	fs := flag.NewFlagSet("run", flag.ExitOnError)
	manifestPath := fs.String("manifest", "", "device manifest json")
	framesPath := fs.String("frames", "", "poll frames jsonl")
	_ = fs.Parse(os.Args[2:])
	if *manifestPath == "" || *framesPath == "" {
		fail(fmt.Errorf("manifest and frames required"))
	}
	frames, err := ingest.LoadFrames(*framesPath)
	if err != nil {
		fail(err)
	}
	if err := ingest.WriteStaging(cfg.StagingPath, cfg.StagingSeqPath, *manifestPath, frames); err != nil {
		fail(err)
	}
	snap, err := staging.Read(cfg.StagingPath)
	if err != nil {
		fail(err)
	}
	m, err := manifest.Load(*manifestPath)
	if err != nil {
		fail(err)
	}
	if err := catalog.RunCatalog(m, snap, cfg.CatalogGenerationPath, cfg.RejectedFramesPath); err != nil {
		fail(err)
	}
	if err := export.RunExport(snap, cfg.CatalogGenerationPath, cfg.DriftCatalogPath); err != nil {
		fail(err)
	}
}

func resolveManifest(snap model.PollStaging) (string, error) {
	if snap.ManifestPath != "" {
		if _, err := os.Stat(snap.ManifestPath); err != nil {
			return "", fmt.Errorf("manifest path from staging: %w", err)
		}
		return snap.ManifestPath, nil
	}
	root := fixtureRoot()
	candidates := []string{
		filepath.Join(root, "manifests", "plant-alpha.json"),
		filepath.Join(root, "manifest.json"),
	}
	for _, p := range candidates {
		h, err := manifest.SHA256File(p)
		if err != nil {
			continue
		}
		if h == snap.ManifestSHA256 {
			return p, nil
		}
	}
	for _, p := range candidates {
		if _, err := os.Stat(p); err == nil {
			return p, nil
		}
	}
	return "", fmt.Errorf("manifest not found under %s", root)
}

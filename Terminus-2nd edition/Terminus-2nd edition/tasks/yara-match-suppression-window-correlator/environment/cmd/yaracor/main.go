package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"yaracor/internal/config"
	"yaracor/internal/correlate"
	"yaracor/internal/export"
	"yaracor/internal/ingest"
	"yaracor/internal/model"
	"yaracor/internal/policy"
	"yaracor/internal/staging"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: yaracor <ingest|correlate|export|run> ...")
		os.Exit(2)
	}
	cfg, err := config.Load("/app/config/correlator.json")
	if err != nil {
		fail(err)
	}
	switch os.Args[1] {
	case "ingest":
		runIngest(cfg)
	case "correlate":
		runCorrelate(cfg)
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
	if d := os.Getenv("YARACOR_FIXTURE_DIR"); d != "" {
		return d
	}
	return "/app/fixtures"
}

func runIngest(cfg model.Config) {
	fs := flag.NewFlagSet("ingest", flag.ExitOnError)
	policyPath := fs.String("policy", "", "soc policy json")
	eventsPath := fs.String("events", "", "yara events jsonl")
	_ = fs.Parse(os.Args[2:])
	if *policyPath == "" || *eventsPath == "" {
		fail(fmt.Errorf("policy and events required"))
	}
	events, err := ingest.LoadEvents(*eventsPath)
	if err != nil {
		fail(err)
	}
	if err := ingest.WriteStaging(cfg.StagingPath, cfg.StagingSeqPath, *policyPath, events); err != nil {
		fail(err)
	}
}

func runCorrelate(cfg model.Config) {
	snap, err := staging.Read(cfg.StagingPath)
	if err != nil {
		fail(err)
	}
	ppath, err := resolvePolicy(snap)
	if err != nil {
		fail(err)
	}
	p, err := policy.Load(ppath)
	if err != nil {
		fail(err)
	}
	if err := correlate.RunCorrelate(p, snap, cfg.CorrelateGenerationPath, cfg.RejectedEventsPath, cfg.DefaultSeverityTier); err != nil {
		fail(err)
	}
}

func runExport(cfg model.Config) {
	snap, err := staging.Read(cfg.StagingPath)
	if err != nil {
		fail(err)
	}
	if err := export.RunExport(snap, cfg.CorrelateGenerationPath, cfg.IncidentBundlePath); err != nil {
		fail(err)
	}
}

func runAll(cfg model.Config) {
	fs := flag.NewFlagSet("run", flag.ExitOnError)
	policyPath := fs.String("policy", "", "soc policy json")
	eventsPath := fs.String("events", "", "yara events jsonl")
	_ = fs.Parse(os.Args[2:])
	if *policyPath == "" || *eventsPath == "" {
		fail(fmt.Errorf("policy and events required"))
	}
	events, err := ingest.LoadEvents(*eventsPath)
	if err != nil {
		fail(err)
	}
	if err := ingest.WriteStaging(cfg.StagingPath, cfg.StagingSeqPath, *policyPath, events); err != nil {
		fail(err)
	}
	snap, err := staging.Read(cfg.StagingPath)
	if err != nil {
		fail(err)
	}
	p, err := policy.Load(*policyPath)
	if err != nil {
		fail(err)
	}
	if err := correlate.RunCorrelate(p, snap, cfg.CorrelateGenerationPath, cfg.RejectedEventsPath, cfg.DefaultSeverityTier); err != nil {
		fail(err)
	}
	if err := export.RunExport(snap, cfg.CorrelateGenerationPath, cfg.IncidentBundlePath); err != nil {
		fail(err)
	}
}

func resolvePolicy(snap model.EventStaging) (string, error) {
	if snap.PolicyPath != "" {
		if _, err := os.Stat(snap.PolicyPath); err == nil {
			return snap.PolicyPath, nil
		}
	}
	root := fixtureRoot()
	candidates := []string{
		filepath.Join(root, "policy", "policy-east.json"),
		filepath.Join(root, "policy.json"),
	}
	for _, p := range candidates {
		h, err := policy.SHA256File(p)
		if err != nil {
			continue
		}
		if h == snap.PolicySHA256 {
			return p, nil
		}
	}
	for _, p := range candidates {
		if _, err := os.Stat(p); err == nil {
			return p, nil
		}
	}
	return "", fmt.Errorf("policy not found under %s", root)
}

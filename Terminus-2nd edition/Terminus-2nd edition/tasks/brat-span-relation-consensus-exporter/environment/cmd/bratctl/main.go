package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/brat-consensus-exporter/internal/config"
	"github.com/terminus/brat-consensus-exporter/internal/consensus"
	"github.com/terminus/brat-consensus-exporter/internal/export"
	"github.com/terminus/brat-consensus-exporter/internal/ingest"
	"github.com/terminus/brat-consensus-exporter/internal/model"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: bratctl <ingest|consensus|export|run> ...")
		os.Exit(2)
	}
	cfg, err := config.Load("/app/config/bratctl.json")
	if err != nil {
		fail(err)
	}
	switch os.Args[1] {
	case "ingest":
		runIngest(cfg)
	case "consensus":
		runConsensus(cfg)
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

func runIngest(cfg model.Config) {
	fs := flag.NewFlagSet("ingest", flag.ExitOnError)
	project := fs.String("project", "", "annotation project directory")
	_ = fs.Parse(os.Args[2:])
	if *project == "" {
		fail(fmt.Errorf("--project required"))
	}
	if err := ingest.IngestProject(cfg.StagingPath, cfg.StagingSeqPath, *project); err != nil {
		fail(err)
	}
}

func runConsensus(cfg model.Config) {
	if err := consensus.RunConsensus(cfg.StagingPath, cfg.ConsensusGenerationPath); err != nil {
		fail(err)
	}
}

func runExport(cfg model.Config) {
	if err := export.RunExport(cfg.StagingPath, cfg.ConsensusGenerationPath, cfg.ConsensusExportPath); err != nil {
		fail(err)
	}
}

func runAll(cfg model.Config) {
	fs := flag.NewFlagSet("run", flag.ExitOnError)
	project := fs.String("project", "", "annotation project directory")
	_ = fs.Parse(os.Args[2:])
	if *project == "" {
		fail(fmt.Errorf("--project required"))
	}
	if err := ingest.IngestProject(cfg.StagingPath, cfg.StagingSeqPath, *project); err != nil {
		fail(err)
	}
	if err := consensus.RunConsensus(cfg.StagingPath, cfg.ConsensusGenerationPath); err != nil {
		fail(err)
	}
	if err := export.RunExport(cfg.StagingPath, cfg.ConsensusGenerationPath, cfg.ConsensusExportPath); err != nil {
		fail(err)
	}
}

package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/sarbctl-curator/internal/config"
	"github.com/terminus/sarbctl-curator/internal/curate"
	"github.com/terminus/sarbctl-curator/internal/emitdelta"
	"github.com/terminus/sarbctl-curator/internal/model"
	scanstage "github.com/terminus/sarbctl-curator/internal/scanstage"
	"github.com/terminus/sarbctl-curator/internal/sarif"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: sarbctl <scan|ingest|curate|emit|export|run> ...")
		os.Exit(2)
	}
	cfg, err := config.Load("/app/config/sarbctl.json")
	if err != nil {
		fail(err)
	}
	switch os.Args[1] {
	case "scan", "ingest":
		runScan(cfg)
	case "curate":
		runCurate(cfg)
	case "emit", "export":
		runEmit(cfg)
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

func runScan(cfg model.Config) {
	fs := flag.NewFlagSet("scan", flag.ExitOnError)
	sarifPath := fs.String("sarif", "", "sarif json path")
	policyPath := fs.String("policy", "", "suppression policy json")
	remapPath := fs.String("remap", "", "path remap json")
	baselinePath := fs.String("baseline", "", "baseline snapshot json")
	_ = fs.Parse(os.Args[2:])
	if *sarifPath == "" || *policyPath == "" || *remapPath == "" || *baselinePath == "" {
		fail(fmt.Errorf("sarif, policy, remap, and baseline required"))
	}
	findings, _, err := sarif.LoadFindings(*sarifPath)
	if err != nil {
		fail(err)
	}
	if err := scanstage.WriteStaging(cfg.StagingPath, cfg.StagingSeqPath, *sarifPath, *policyPath, *remapPath, *baselinePath, findings); err != nil {
		fail(err)
	}
}

func runCurate(cfg model.Config) {
	gen, err := curate.BumpRevision(cfg.BaselineRevisionPath)
	if err != nil {
		fail(err)
	}
	if err := curate.Run(cfg, gen); err != nil {
		fail(err)
	}
}

func runEmit(cfg model.Config) {
	if err := emitdelta.RunPublish(cfg); err != nil {
		fail(err)
	}
}

func runAll(cfg model.Config) {
	fs := flag.NewFlagSet("run", flag.ExitOnError)
	sarifPath := fs.String("sarif", "", "sarif json path")
	policyPath := fs.String("policy", "", "suppression policy json")
	remapPath := fs.String("remap", "", "path remap json")
	baselinePath := fs.String("baseline", "", "baseline snapshot json")
	_ = fs.Parse(os.Args[2:])
	if *sarifPath == "" || *policyPath == "" || *remapPath == "" || *baselinePath == "" {
		fail(fmt.Errorf("sarif, policy, remap, and baseline required"))
	}
	findings, _, err := sarif.LoadFindings(*sarifPath)
	if err != nil {
		fail(err)
	}
	if err := scanstage.WriteStaging(cfg.StagingPath, cfg.StagingSeqPath, *sarifPath, *policyPath, *remapPath, *baselinePath, findings); err != nil {
		fail(err)
	}
	gen, err := curate.BumpRevision(cfg.BaselineRevisionPath)
	if err != nil {
		fail(err)
	}
	if err := curate.Run(cfg, gen); err != nil {
		fail(err)
	}
	if err := emitdelta.RunPublish(cfg); err != nil {
		fail(err)
	}
}

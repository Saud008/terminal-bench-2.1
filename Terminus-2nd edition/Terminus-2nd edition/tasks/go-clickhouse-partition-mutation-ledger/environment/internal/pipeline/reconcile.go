package pipeline

import (
	"github.com/terminus/chmutled/internal/config"
	"github.com/terminus/chmutled/internal/ledgerbuf"
	"github.com/terminus/chmutled/internal/meta"
	"github.com/terminus/chmutled/internal/mutcmd"
	"github.com/terminus/chmutled/internal/replic"
)

// RunReconcile is the ingest stage of the partition mutation ledger pipeline.
func RunReconcile(metaDir, mutDir, repDir, cfgDir, stagingPath string) error {
	parts, err := meta.LoadDir(metaDir)
	if err != nil {
		return err
	}
	muts, err := mutcmd.LoadDir(mutDir)
	if err != nil {
		return err
	}
	reps, err := replic.LoadDir(repDir)
	if err != nil {
		return err
	}
	cfg, err := config.Load(cfgDir)
	if err != nil {
		return err
	}
	partIndex := buildPartIndex(parts)
	lagByPart := lagMap(reps)
	maxVer := maxVersionByPartition(muts)
	staged := assembleStagedRows(muts, partIndex, lagByPart, maxVer, cfg.Lag.MaxLagSec)
	return ledgerbuf.Write(stagingPath, staged)
}

package pipeline

import (
	"github.com/terminus/chmutled/internal/config"
	"github.com/terminus/chmutled/internal/detach"
	"github.com/terminus/chmutled/internal/ledgerbuf"
	"github.com/terminus/chmutled/internal/meta"
	"github.com/terminus/chmutled/internal/model"
	"github.com/terminus/chmutled/internal/mutcmd"
	"github.com/terminus/chmutled/internal/mutver"
	"github.com/terminus/chmutled/internal/partkey"
	"github.com/terminus/chmutled/internal/readiness"
	"github.com/terminus/chmutled/internal/replic"
	"github.com/terminus/chmutled/internal/replag"
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
	var staged []model.StagedMutation
	for _, m := range muts {
		pi, ok := partIndex[m.PartitionID]
		if !ok {
			continue
		}
		lagMax := lagByPart[m.PartitionID]
		detached := detach.IsDetached(pi.detachedFlags)
		state := readiness.State(detached, lagMax, cfg.Lag.MaxLagSec, m.MutationVersion, maxVer[m.PartitionID])
		staged = append(staged, model.StagedMutation{
			MutationID: m.MutationID, PartitionID: m.PartitionID, MutationVersion: m.MutationVersion,
			TableName: pi.table, ReadinessState: state, ReplicaLagMax: lagMax, PartCount: pi.partCount,
			IssuedAt: m.IssuedAt,
		})
	}
	return ledgerbuf.Write(stagingPath, staged)
}

type partInfo struct {
	table         string
	partCount     int
	detachedFlags []bool
}

func buildPartIndex(parts []model.PartMeta) map[string]partInfo {
	idx := map[string]partInfo{}
	for _, p := range parts {
		pid := partkey.PartitionID(p)
		cur := idx[pid]
		cur.table = p.TableName
		cur.partCount += p.PartCount
		cur.detachedFlags = append(cur.detachedFlags, p.Detached)
		idx[pid] = cur
	}
	return idx
}

func lagMap(reps []model.ReplicaLog) map[string]int {
	m := map[string][]int{}
	for _, r := range reps {
		m[r.PartitionID] = append(m[r.PartitionID], r.LagSec)
	}
	out := map[string]int{}
	for pid, lags := range m {
		out[pid] = replag.MaxLag(lags)
	}
	return out
}

func maxVersionByPartition(muts []model.MutCmd) map[string]int {
	out := map[string]int{}
	for _, m := range muts {
		cur := out[m.PartitionID]
		if mutver.Greater(m.MutationVersion, cur) {
			out[m.PartitionID] = m.MutationVersion
		}
	}
	return out
}

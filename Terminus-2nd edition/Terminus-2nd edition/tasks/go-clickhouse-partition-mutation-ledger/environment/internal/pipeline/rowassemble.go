package pipeline

import (
	"github.com/terminus/chmutled/internal/detach"
	"github.com/terminus/chmutled/internal/model"
	"github.com/terminus/chmutled/internal/readiness"
)

func assembleStagedRows(
	muts []model.MutCmd,
	partIndex map[string]partInfo,
	lagByPart map[string]int,
	maxVer map[string]int,
	threshold int,
) []model.StagedMutation {
	var staged []model.StagedMutation
	for _, m := range muts {
		pi, ok := partIndex[m.PartitionID]
		if !ok {
			continue
		}
		lagMax := lagByPart[m.PartitionID]
		detached := detach.IsDetached(pi.detachedFlags)
		state := readiness.State(detached, lagMax, threshold, m.MutationVersion, maxVer[m.PartitionID])
		staged = append(staged, model.StagedMutation{
			MutationID: m.MutationID, PartitionID: m.PartitionID, MutationVersion: m.MutationVersion,
			TableName: pi.table, ReadinessState: state, ReplicaLagMax: lagMax, PartCount: pi.partCount,
			IssuedAt: m.IssuedAt,
		})
	}
	return staged
}

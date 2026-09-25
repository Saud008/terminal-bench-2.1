package pipeline

import (
	"github.com/terminus/chmutled/internal/model"
	"github.com/terminus/chmutled/internal/mutver"
)

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

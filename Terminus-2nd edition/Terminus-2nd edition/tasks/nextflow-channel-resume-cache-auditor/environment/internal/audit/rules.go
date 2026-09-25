package audit

import (
	"fmt"

	"github.com/terminus/nfresume/internal/lineage"
	"github.com/terminus/nfresume/internal/model"
)

func ruleFindings(snap model.StageSnapshot, t model.StagedTask) []model.UnsafeFinding {
	var out []model.UnsafeFinding

	if t.Cached && t.PriorDigest != "" && t.ContainerDigest != t.PriorDigest {
		out = append(out, model.UnsafeFinding{
			TaskID: t.TaskID,
			Rule:   "digest_drift",
			Detail: fmt.Sprintf("cached digest %s != prior %s", t.ContainerDigest, t.PriorDigest),
		})
	}

	if t.ExpansionHash != "" && t.ComputedExpand != t.ExpansionHash {
		out = append(out, model.UnsafeFinding{
			TaskID: t.TaskID,
			Rule:   "glob_expansion_mismatch",
			Detail: fmt.Sprintf("recorded %s computed %s", t.ExpansionHash, t.ComputedExpand),
		})
	}

	expected := lineage.ComputeLineageDigest(t.ParentHashes, t.Hash)
	if expected != t.LineageDigest {
		out = append(out, model.UnsafeFinding{
			TaskID: t.TaskID,
			Rule:   "lineage_break",
			Detail: fmt.Sprintf("staged %s expected %s", t.LineageDigest, expected),
		})
	}

	if t.Attempt > 1 && t.Cached && t.PriorExitStatus != nil && *t.PriorExitStatus == 0 {
		out = append(out, model.UnsafeFinding{
			TaskID: t.TaskID,
			Rule:   "retry_stale_cache",
			Detail: fmt.Sprintf("attempt %d cached after prior exit %d", t.Attempt, *t.PriorExitStatus),
		})
	}

	return out
}

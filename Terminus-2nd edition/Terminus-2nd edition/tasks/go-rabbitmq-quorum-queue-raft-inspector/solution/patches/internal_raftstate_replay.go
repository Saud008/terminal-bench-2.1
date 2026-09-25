package ocfcore

import (
	"crypto/sha256"
	"encoding/hex"
	"sort"

	"github.com/terminus/qqraftctl/internal/canonical"
	"github.com/terminus/qqraftctl/internal/votercfg"
	"github.com/terminus/qqraftctl/internal/model"
)

type ReplayResult struct {
	Staging model.Staging
}

type ReplayBaseline struct {
	Membership  []string
	QueueStates map[string]int64
	CommitIndex int64
	CurrentTerm int64
	EpochTerm   int64
}

func Replay(cluster string, entries []model.LogEntry, truncatedBefore int64, base ReplayBaseline) ReplayResult {
	elect := ElectionState{CurrentTerm: base.CurrentTerm}
	commit := CommitTracker{CommitIndex: base.CommitIndex}
	mem := votercfg.Set{Voters: append([]string(nil), base.Membership...), EpochTerm: base.EpochTerm}
	queues := map[string]int64{}
	for k, v := range base.QueueStates {
		queues[k] = v
	}
	var pending []model.LogEntry

	for _, e := range entries {
		switch e.Kind {
		case "election":
			ApplyElection(&elect, e)
		case "commit":
			ApplyEntry(&commit, e)
		case "config":
			votercfg.ApplyConfig(&mem, e)
		case "queue":
			pending = append(pending, e)
		}
	}

	for _, e := range pending {
		if Committed(commit, e.Index) {
			if v, ok := e.Payload["messages"].(float64); ok {
				queues[e.QueueID] = int64(v)
			}
		}
	}

	sort.Strings(mem.Voters)
	st := model.Staging{
		Cluster:         cluster,
		CommitIndex:     commit.CommitIndex,
		CurrentTerm:     elect.CurrentTerm,
		LeaderID:        elect.LeaderID,
		Membership:      append([]string(nil), mem.Voters...),
		QueueStates:     queues,
		TruncatedBefore: truncatedBefore,
	}
	st.ReplayDigest = digestStaging(st)
	return ReplayResult{Staging: st}
}

func digestStaging(st model.Staging) string {
	qs := map[string]int64{}
	keys := make([]string, 0, len(st.QueueStates))
	for k := range st.QueueStates {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		qs[k] = st.QueueStates[k]
	}
	body := map[string]any{
		"cluster": st.Cluster, "commit_index": st.CommitIndex,
		"current_term": st.CurrentTerm, "leader_id": st.LeaderID,
		"membership": st.Membership, "queue_states": qs,
		"truncated_before": st.TruncatedBefore,
	}
	sum := sha256.Sum256(canonical.MarshalMap(body))
	return hex.EncodeToString(sum[:])
}

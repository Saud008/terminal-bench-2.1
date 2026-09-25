package workpad

import (
	"crypto/sha256"
	"encoding/hex"
	"sort"

	"github.com/terminus/qqraftctl/internal/canonical"
	"github.com/terminus/qqraftctl/internal/model"
)

func ComputeRaftSeal(st model.Staging) string {
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
		"membership_epoch": st.CurrentTerm,
	}
	sum := sha256.Sum256(canonical.MarshalMap(body))
	return hex.EncodeToString(sum[:])
}

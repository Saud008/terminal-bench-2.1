package workpad

import (
	"crypto/sha256"
	"encoding/hex"

	"github.com/terminus/qqraftctl/internal/canonical"
	"github.com/terminus/qqraftctl/internal/model"
)

func ComputeRaftSeal(st model.Staging) string {
	body := map[string]any{
		"cluster": st.Cluster, "commit_index": st.CommitIndex,
		"current_term": st.CurrentTerm, "leader_id": st.LeaderID,
		"membership": st.Membership, "queue_states": st.QueueStates,
	}
	sum := sha256.Sum256(canonical.MarshalMap(body))
	return hex.EncodeToString(sum[:])
}

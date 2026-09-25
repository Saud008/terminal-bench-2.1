package ocfcore

import "github.com/terminus/qqraftctl/internal/model"

type ElectionState struct {
    CurrentTerm int64
    LeaderID    string
}

func ApplyElection(st *ElectionState, entry model.LogEntry) {
    nodeID, _ := entry.Payload["node_id"].(string)
    role, _ := entry.Payload["role"].(string)
    if entry.Term >= st.CurrentTerm {
        st.CurrentTerm = entry.Term
        if role == "leader" {
            st.LeaderID = nodeID
        }
    }
}

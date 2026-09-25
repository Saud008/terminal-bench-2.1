package query

import "github.com/terminus/cadence-replay/internal/model"

// ProcessQuery evaluates a workflow query task against heartbeat progress.
func ProcessQuery(state *model.RuntimeState, q model.QueryTask) {
	if q.IsResetWorkflow {
		state.QueryResults = append(state.QueryResults, model.QueryResult{
			QueryID:  q.QueryID,
			Accepted: true,
			Reason:   "reset bypass",
		})
		return
	}
	if state.LastProgressSeq < q.RequiredProgressSeq {
		state.QueryResults = append(state.QueryResults, model.QueryResult{
			QueryID:  q.QueryID,
			Accepted: false,
			Reason:   "heartbeat progress insufficient",
		})
		return
	}
	state.QueryResults = append(state.QueryResults, model.QueryResult{
		QueryID:  q.QueryID,
		Accepted: true,
		Reason:   "ok",
	})
}

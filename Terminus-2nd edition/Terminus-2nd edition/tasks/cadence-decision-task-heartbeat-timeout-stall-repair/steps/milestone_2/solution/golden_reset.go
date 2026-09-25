package query

import "github.com/terminus/cadence-replay/internal/model"

func ProcessQuery(state *model.RuntimeState, q model.QueryTask) {
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

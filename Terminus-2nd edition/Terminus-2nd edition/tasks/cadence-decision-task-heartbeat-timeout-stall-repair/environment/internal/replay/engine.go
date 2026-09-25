package replay

import (
	"sort"

	"github.com/terminus/cadence-replay/internal/heartbeat"
	"github.com/terminus/cadence-replay/internal/history"
	"github.com/terminus/cadence-replay/internal/model"
	"github.com/terminus/cadence-replay/internal/query"
	"github.com/terminus/cadence-replay/internal/sticky"
	"github.com/terminus/cadence-replay/internal/timeout"
)

type timelineKind int

const (
	kindHistory timelineKind = iota
	kindHeartbeat
	kindTimeout
	kindQuery
	kindPoll
)

type timelineItem struct {
	atMs int64
	kind timelineKind
	idx  int
}

func NewState(sc model.Scenario) *model.RuntimeState {
	return &model.RuntimeState{
		Scenario:     sc,
		SeenEventIDs: make(map[int]bool),
	}
}

func buildTimeline(sc model.Scenario) []timelineItem {
	var items []timelineItem
	for i, ev := range sc.HistoryEvents {
		items = append(items, timelineItem{atMs: ev.AtMs, kind: kindHistory, idx: i})
	}
	for i, hb := range sc.Heartbeats {
		items = append(items, timelineItem{atMs: hb.AtMs, kind: kindHeartbeat, idx: i})
	}
	for i, ms := range sc.TimeoutChecksMs {
		items = append(items, timelineItem{atMs: ms, kind: kindTimeout, idx: i})
	}
	for i, q := range sc.QueryTasks {
		items = append(items, timelineItem{atMs: q.AtMs, kind: kindQuery, idx: i})
	}
	if sc.DecisionPollMs > 0 {
		items = append(items, timelineItem{atMs: sc.DecisionPollMs, kind: kindPoll, idx: 0})
	}
	sort.Slice(items, func(i, j int) bool {
		if items[i].atMs == items[j].atMs {
			return items[i].kind < items[j].kind
		}
		return items[i].atMs < items[j].atMs
	})
	return items
}

func Run(sc model.Scenario) *model.ReplayReport {
	state := NewState(sc)
	for _, item := range buildTimeline(sc) {
		switch item.kind {
		case kindHistory:
			history.ApplyEvent(state, sc.HistoryEvents[item.idx])
		case kindHeartbeat:
			heartbeat.ApplyHeartbeat(state, sc.Heartbeats[item.idx])
		case kindTimeout:
			timeout.CheckTimeout(state, sc.TimeoutChecksMs[item.idx])
		case kindQuery:
			query.ProcessQuery(state, sc.QueryTasks[item.idx])
		case kindPoll:
			sticky.EvaluateDecisionPoll(state, sc.DecisionPollMs)
		}
	}
	return &model.ReplayReport{
		WorkflowID:             sc.WorkflowID,
		VisibilityDeadlineMs:   state.VisibilityDeadlineMs,
		LastProgressSeq:        state.LastProgressSeq,
		StickyPartition:        state.StickyPartition,
		HistoryCursorSeq:       state.HistoryCursorSeq,
		HistoryEventsApplied:   nonNilStrings(state.AppliedNames),
		DuplicateEventsSkipped: state.DuplicateSkipped,
		DecisionTaskLost:       state.DecisionTaskLost,
		TimedOut:               state.TimedOut,
		QueryResults:           nonNilQueries(state.QueryResults),
		LostDecisionReason:     state.LostDecisionReason,
		LastHeartbeatMs:        state.LastHeartbeatMs,
	}
}

func nonNilStrings(in []string) []string {
	if len(in) == 0 {
		return []string{}
	}
	return append([]string(nil), in...)
}

func nonNilQueries(in []model.QueryResult) []model.QueryResult {
	if len(in) == 0 {
		return []model.QueryResult{}
	}
	return append([]model.QueryResult(nil), in...)
}

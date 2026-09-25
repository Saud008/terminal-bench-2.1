package simulate

import (
	"github.com/terminus/ballotmesh/internal/ballot"
	"github.com/terminus/ballotmesh/internal/config"
	"github.com/terminus/ballotmesh/internal/export"
	"github.com/terminus/ballotmesh/internal/frame"
	"github.com/terminus/ballotmesh/internal/ingest"
	"github.com/terminus/ballotmesh/internal/model"
	"github.com/terminus/ballotmesh/internal/staging"
	"github.com/terminus/ballotmesh/internal/surveyor"
	"github.com/terminus/ballotmesh/internal/topology"
	"github.com/terminus/ballotmesh/internal/ttl"
)

type Result struct {
	Snapshot model.SurveySnapshot
}

func Run(m model.Mesh) (Result, error) {
	m = ingest.Normalize(m)
	collector := surveyor.NewCollector()
	merge := ballot.NewMergeState()
	tracker := ttl.NewTracker(m.DefaultTTLMS)
	pipeDrained := map[string]bool{}
	latestVote := map[string]int{}
	weights := map[string]int{}

	empty := model.SurveySnapshot{
		SnapshotVersion: 1,
		TableSuffix:       config.TableSuffix(),
		MeshID:            m.MeshID,
		SurveyID:          m.SurveyID,
		Records:           []model.TallyRecord{},
		FinalTally:        map[string]int{},
		PartialRespondents: []string{},
		ExportReady:       false,
	}
	if err := staging.WriteEarlyManifest(empty); err != nil {
		return Result{}, err
	}

	records := []model.TallyRecord{}
	respondentsSeen := map[string]bool{}

	for idx, ev := range m.Events {
		rec := model.TallyRecord{
			EventIndex: idx,
			OffsetMS:   ev.OffsetMS,
			EventType:  ev.Type,
			Respondent: ev.Respondent,
		}

		switch ev.Type {
		case "start":
			collector.OnStart()
			for _, e := range m.Events {
				if e.Type == "ballot" && e.Respondent != "" {
					respondentsSeen[e.Respondent] = true
				}
			}
			for r := range respondentsSeen {
				tracker.OnStart(r, ev.OffsetMS)
				weights[r] = topology.VoteWeight(m.Topology, r)
			}
		case "ballot":
			header := frame.DecodeHeader(ev.HeaderHex)
			rec.SurveyIDHeader = frame.ParseSurveyID(header)
			rec.SurveyIDOK = frame.SurveyIDMatches(header, m.SurveyID)
			rec.PipeDrained = pipeDrained[ev.Respondent]
			collector.OnBallot(ev.Respondent)
			latestVote[ev.Respondent] = ev.Vote
			sealed := collector.IsSealed(ev.Respondent)
			rec.Sealed = sealed
			rec.TTLExpiresMS = tracker.ExpiresMS(ev.Respondent)
			rec.TopologyWeight = topology.VoteWeight(m.Topology, ev.Respondent)
			if !rec.SurveyIDOK {
				rec.RejectReason = "survey_id_mismatch"
			} else if !tracker.Active(ev.Respondent, ev.OffsetMS) {
				rec.RejectReason = "ttl_expired"
			} else {
				merge.StageVote(ev.Respondent, ev.Vote, sealed)
				rec.TallyIncluded = sealed
			}
			rec.StateAfter = string(collector.State())
		case "pipe_drained":
			pipeDrained[ev.Respondent] = true
			collector.OnPipeDrained(ev.Respondent)
			rec.PipeDrained = true
			fsmSealed := collector.IsSealed(ev.Respondent)
			active := tracker.Active(ev.Respondent, ev.OffsetMS)
			rec.Sealed = fsmSealed && active
			if v, ok := latestVote[ev.Respondent]; ok && fsmSealed && active {
				merge.StageVote(ev.Respondent, v, true)
				rec.TallyIncluded = true
			}
			rec.StateAfter = string(collector.State())
		case "reconnect":
			tracker.OnReconnect(ev.Respondent, ev.OffsetMS)
			rec.ReconnectReset = tracker.ExpiresMS(ev.Respondent) == ev.OffsetMS+m.DefaultTTLMS
			rec.Respondent = ev.Respondent
			rec.TTLExpiresMS = tracker.ExpiresMS(ev.Respondent)
			rec.StateAfter = string(collector.State())
		case "deadline":
			collector.OnDeadline()
			merge.FinalizeAtDeadline()
			rec.StateAfter = string(collector.State())
		case "close":
			collector.OnClose()
			rec.StateAfter = string(collector.State())
		}
		records = append(records, rec)
	}

	merge.FinalizeAtDeadline()
	final := merge.Final
	if !merge.DeadlineHit {
		final = map[string]int{}
	}
	total := export.SumWeighted(final, weights)

	snap := model.SurveySnapshot{
		SnapshotVersion:    1,
		TableSuffix:          config.TableSuffix(),
		MeshID:               m.MeshID,
		SurveyID:             m.SurveyID,
		Records:              records,
		FinalTally:           final,
		TotalWeighted:        total,
		PartialRespondents:   merge.PartialRespondents(),
		ExportReady:          true,
	}
	if err := staging.WriteSnapshot(snap); err != nil {
		return Result{}, err
	}
	return Result{Snapshot: snap}, nil
}

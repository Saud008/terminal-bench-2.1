package correlate

import (
	"encoding/json"
	"os"
	"sort"

	"yaracor/internal/criticality"
	"yaracor/internal/dedupe"
	"yaracor/internal/model"
	"yaracor/internal/quarantine"
	"yaracor/internal/rules"
	"yaracor/internal/suppression"
)

func Build(p model.Policy, snap model.EventStaging, gen int, defaultTier string) (model.CorrelateGeneration, []model.RejectedEvent, error) {
	var valid []model.ScanEvent
	for _, ev := range snap.Events {
		if rules.RevisionActive(p, ev) {
			valid = append(valid, ev)
		}
	}
	dupes := dedupe.ClassifyDuplicates(valid)
	var rejected []model.RejectedEvent
	var incidents []model.IncidentRow
	for _, ev := range snap.Events {
		if !rules.RevisionActive(p, ev) {
			rejected = append(rejected, model.RejectedEvent{EventID: ev.EventID, Reason: "stale_rule_revision"})
			continue
		}
		row := model.IncidentRow{
			EventID:      ev.EventID,
			AssetID:      ev.AssetID,
			SampleSHA256: ev.SampleSHA256,
			RuleName:     ev.RuleName,
			RuleRevision: ev.RuleRevision,
			DetectedMs:   ev.DetectedMs,
			SeverityTier: criticality.EffectiveTier(p, ev, defaultTier),
			Actionable:   true,
		}
		if dupes[ev.EventID] {
			row.Suppressed = true
			row.SuppressionReason = "duplicate_sample"
			row.Actionable = false
		}
		if ok, ticket := suppression.TicketMatches(p, ev); ok {
			row.Suppressed = true
			row.SuppressionReason = "suppression_ticket:" + ticket
			row.Actionable = false
		}
		if quarantine.IsQuarantined(p, ev) {
			row.Suppressed = true
			row.SuppressionReason = "quarantine_active"
			row.Actionable = false
		}
		incidents = append(incidents, row)
	}
	sort.Slice(incidents, func(i, j int) bool {
		if incidents[i].DetectedMs == incidents[j].DetectedMs {
			return incidents[i].EventID < incidents[j].EventID
		}
		return incidents[i].DetectedMs < incidents[j].DetectedMs
	})
	return model.CorrelateGeneration{
		Generation:        gen,
		StagingGeneration: snap.StagingGeneration,
		PolicySHA256:      snap.PolicySHA256,
		Incidents:         incidents,
	}, rejected, nil
}

func WriteRejected(path string, rows []model.RejectedEvent) error {
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	enc := json.NewEncoder(f)
	for _, row := range rows {
		if err := enc.Encode(row); err != nil {
			return err
		}
	}
	return nil
}

func RunCorrelate(p model.Policy, snap model.EventStaging, genPath, rejectedPath, defaultTier string) error {
	prev, _ := ReadGeneration(genPath)
	gen := prev.Generation + 1
	if gen < 1 {
		gen = 1
	}
	corr, rejected, err := Build(p, snap, gen, defaultTier)
	if err != nil {
		return err
	}
	if err := WriteGeneration(genPath, corr); err != nil {
		return err
	}
	return WriteRejected(rejectedPath, rejected)
}

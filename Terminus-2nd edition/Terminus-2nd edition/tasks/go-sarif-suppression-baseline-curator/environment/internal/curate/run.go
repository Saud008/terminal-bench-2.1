package curate

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/sarbctl-curator/internal/dedupe"
	"github.com/terminus/sarbctl-curator/internal/fingerprint"
	"github.com/terminus/sarbctl-curator/internal/model"
	"github.com/terminus/sarbctl-curator/internal/policy"
	"github.com/terminus/sarbctl-curator/internal/remap"
	"github.com/terminus/sarbctl-curator/internal/rules"
	"github.com/terminus/sarbctl-curator/internal/sarif"
	"github.com/terminus/sarbctl-curator/internal/staging"
	"github.com/terminus/sarbctl-curator/internal/suppress"
)

func Run(cfg model.Config, gen int) error {
	snap, err := staging.Read(cfg.StagingPath)
	if err != nil {
		return err
	}
	pol, err := policy.Load(snap.PolicyPath)
	if err != nil {
		return err
	}
	rmap, err := remap.Load(snap.RemapPath)
	if err != nil {
		return err
	}
	base, err := sarif.LoadBaseline(snap.BaselinePath)
	if err != nil {
		return err
	}
	baseByKey := map[string]model.BaselineFinding{}
	for _, b := range base.Findings {
		rk := rules.CanonicalKey(b.Tool, b.RuleID, pol.RulesCatalog)
		uri := remap.Apply(b.URI, rmap)
		key := rk + "|" + uri + "|" + lineKey(b.StartLine)
		baseByKey[key] = b
	}
	ruleKeyFn := func(f model.Finding) string {
		return rules.CanonicalKey(f.Tool, f.RuleID, pol.RulesCatalog)
	}
	remapFn := func(uri string) string { return remap.Apply(uri, rmap) }
	collapsed := dedupe.Collapse(snap.Findings, ruleKeyFn, remapFn)
	var entries []model.CuratedEntry
	var rejected []model.RejectedFinding
	for _, f := range collapsed {
		rk := ruleKeyFn(f)
		uri := remapFn(f.URI)
		if suppress.IsExpired(pol, rk, uri, f.ObservedAt) {
			rejected = append(rejected, model.RejectedFinding{FindingID: f.FindingID, Reason: "suppression_expired"})
			continue
		}
		pf := fingerprint.Physical(rk, uri, f.StartLine, f.StartColumn)
		key := rk + "|" + uri + "|" + lineKey(f.StartLine)
		baseRow, ok := baseByKey[key]
		drift := false
		if ok {
			drift = fingerprint.Drift(rk, uri, f.Fingerprint, baseRow.Fingerprint)
		}
		sup := suppress.IsSuppressed(pol, rk, uri, f.ObservedAt)
		entries = append(entries, model.CuratedEntry{
			FindingID:     f.FindingID,
			RuleKey:       rk,
			Level:         f.Level,
			URI:           uri,
			StartLine:     f.StartLine,
			StartColumn:   f.StartColumn,
			Fingerprint:   f.Fingerprint,
			PhysicalFP:    pf,
			Suppressed:    sup,
			DriftFromBase: drift,
		})
	}
	rev := model.BaselineRevision{
		ReconcileRevision: gen,
		ScanRevision:      snap.ScanRevision,
		SarifSHA256:       snap.SarifSHA256,
		PolicySHA256:      snap.PolicySHA256,
		Entries:           entries,
	}
	if err := writeRevision(cfg.BaselineRevisionPath, rev); err != nil {
		return err
	}
	return writeRejected(cfg.RejectedFindingsPath, rejected)
}

func lineKey(v int) string {
	return fmt.Sprintf("%d", v)
}

func writeRevision(path string, rev model.BaselineRevision) error {
	raw, err := json.MarshalIndent(rev, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}

func writeRejected(path string, rows []model.RejectedFinding) error {
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	for _, row := range rows {
		raw, _ := json.Marshal(row)
		if _, err := f.Write(append(raw, '\n')); err != nil {
			return err
		}
	}
	return nil
}

func ReadRevision(path string) (model.BaselineRevision, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.BaselineRevision{}, err
	}
	var rev model.BaselineRevision
	if err := json.Unmarshal(raw, &rev); err != nil {
		return model.BaselineRevision{}, err
	}
	return rev, nil
}

func BumpRevision(path string) (int, error) {
	rev := 0
	if raw, err := os.ReadFile(path); err == nil {
		var prev model.BaselineRevision
		if json.Unmarshal(raw, &prev) == nil {
			rev = prev.ReconcileRevision
		}
	}
	return rev + 1, nil
}

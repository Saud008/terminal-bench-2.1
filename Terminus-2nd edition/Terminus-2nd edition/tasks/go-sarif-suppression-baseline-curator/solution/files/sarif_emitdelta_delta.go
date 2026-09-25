package emitdelta

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	scanstage "github.com/terminus/sarbctl-curator/internal/scanstage"
	"github.com/terminus/sarbctl-curator/internal/model"
	"github.com/terminus/sarbctl-curator/internal/policy"
	"github.com/terminus/sarbctl-curator/internal/remap"
	"github.com/terminus/sarbctl-curator/internal/curate"
	"github.com/terminus/sarbctl-curator/internal/rules"
	"github.com/terminus/sarbctl-curator/internal/sarif"
	"github.com/terminus/sarbctl-curator/internal/staging"
)

func deltaDigest(body map[string]any) string {
	delete(body, "delta_digest")
	keys := make([]string, 0, len(body))
	for k := range body {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var buf bytes.Buffer
	buf.WriteByte('{')
	for i, k := range keys {
		if i > 0 {
			buf.WriteByte(',')
		}
		kb, _ := json.Marshal(k)
		buf.Write(kb)
		buf.WriteByte(':')
		vb, _ := json.Marshal(body[k])
		buf.Write(vb)
	}
	buf.WriteByte('}')
	sum := sha256.Sum256(buf.Bytes())
	return hex.EncodeToString(sum[:])
}

func BuildDelta(rev model.BaselineRevision, base model.BaselineSnapshot, pol model.Policy, rmap model.RemapConfig) model.FindingDelta {
	curKeys := map[string]model.CuratedEntry{}
	for _, e := range rev.Entries {
		curKeys[curateEntryKey(e.RuleKey, e.URI, e.StartLine)] = e
	}
	baseKeys := map[string]model.BaselineFinding{}
	for _, b := range base.Findings {
		rk := rules.CanonicalKey(b.Tool, b.RuleID, pol.RulesCatalog)
		uri := remap.Apply(b.URI, rmap)
		baseKeys[curateEntryKey(rk, uri, b.StartLine)] = b
	}
	var rows []model.DeltaRow
	for key, e := range curKeys {
		if e.DriftFromBase {
			rows = append(rows, model.DeltaRow{
				FindingID: e.FindingID, RuleKey: e.RuleKey, URI: e.URI, StartLine: e.StartLine,
				Category: "drift", Fingerprint: e.Fingerprint,
			})
			continue
		}
		if _, ok := baseKeys[key]; !ok {
			rows = append(rows, model.DeltaRow{
				FindingID: e.FindingID, RuleKey: e.RuleKey, URI: e.URI, StartLine: e.StartLine,
				Category: "new", Fingerprint: e.Fingerprint,
			})
			continue
		}
		if e.Suppressed {
			rows = append(rows, model.DeltaRow{
				FindingID: e.FindingID, RuleKey: e.RuleKey, URI: e.URI, StartLine: e.StartLine,
				Category: "suppressed", Fingerprint: e.Fingerprint,
			})
			continue
		}
		rows = append(rows, model.DeltaRow{
			FindingID: e.FindingID, RuleKey: e.RuleKey, URI: e.URI, StartLine: e.StartLine,
			Category: "unchanged", Fingerprint: e.Fingerprint,
		})
	}
	for key, b := range baseKeys {
		if _, ok := curKeys[key]; ok {
			continue
		}
		rk := rules.CanonicalKey(b.Tool, b.RuleID, pol.RulesCatalog)
		uri := remap.Apply(b.URI, rmap)
		rows = append(rows, model.DeltaRow{
			FindingID: b.FindingID, RuleKey: rk, URI: uri, StartLine: b.StartLine,
			Category: "removed", Fingerprint: b.Fingerprint,
		})
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].Category == rows[j].Category {
			return rows[i].FindingID < rows[j].FindingID
		}
		return rows[i].Category < rows[j].Category
	})
	out := model.FindingDelta{
		ReconcileRevision: rev.ReconcileRevision,
		ScanRevision:      rev.ScanRevision,
		Rows:              rows,
	}
	raw, _ := json.Marshal(out)
	var m map[string]any
	_ = json.Unmarshal(raw, &m)
	out.DeltaDigest = deltaDigest(m)
	return out
}

func curateEntryKey(rk, uri string, line int) string {
	return rk + "|" + uri + "|" + fmt.Sprintf("%d", line)
}

func WriteDelta(path string, delta model.FindingDelta) error {
	raw, err := json.MarshalIndent(delta, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}

func RunPublish(cfg model.Config) error {
	snap, err := staging.Read(cfg.StagingPath)
	if err != nil {
		return err
	}
	rev, err := curate.ReadRevision(cfg.BaselineRevisionPath)
	if err != nil {
		return err
	}
	if rev.ReconcileRevision < 1 {
		return fmt.Errorf("reconcile_revision must be > 0")
	}
	if rev.ScanRevision != snap.ScanRevision {
		return fmt.Errorf("scan_revision mismatch")
	}
	want := scanstage.ComputeFindingsDigest(snap.Findings)
	if snap.FindingsDigest != want {
		return fmt.Errorf("findings_digest mismatch")
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
	delta := BuildDelta(rev, base, pol, rmap)
	return WriteDelta(cfg.FindingDeltaPath, delta)
}

func ValidateRevision(rev model.BaselineRevision) error {
	if rev.ReconcileRevision < 1 {
		return fmt.Errorf("reconcile_revision must be > 0")
	}
	return nil
}

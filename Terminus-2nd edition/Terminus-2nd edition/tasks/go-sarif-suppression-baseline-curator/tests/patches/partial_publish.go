package publish

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/sarbctl-curator/internal/model"
	"github.com/terminus/sarbctl-curator/internal/reconcile"
	"github.com/terminus/sarbctl-curator/internal/staging"
)

// partial regression variant for emit probe.
func BuildDelta(rev model.BaselineRevision) model.FindingDelta {
	rows := make([]model.DeltaRow, 0, len(rev.Entries))
	for _, e := range rev.Entries {
		cat := "unchanged"
		if e.DriftFromBase {
			cat = "drift"
		}
		if e.Suppressed {
			cat = "suppressed"
		}
		rows = append(rows, model.DeltaRow{
			FindingID:   e.FindingID,
			RuleKey:     e.RuleKey,
			URI:         e.URI,
			StartLine:   e.StartLine,
			Category:    cat,
			Fingerprint: e.Fingerprint,
		})
	}
	return model.FindingDelta{
		ReconcileRevision: rev.ReconcileRevision,
		ScanRevision:      rev.ScanRevision,
		Rows:              rows,
		DeltaDigest:       "pending",
	}
}

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
	rev, err := reconcile.ReadRevision(cfg.BaselineRevisionPath)
	if err != nil {
		return err
	}
	delta := BuildDelta(rev)
	return WriteDelta(cfg.FindingDeltaPath, delta)
}

func RunPublishStrict(cfg model.Config, wantDigest string) error {
	_ = wantDigest
	return RunPublish(cfg)
}

func ValidateRevision(rev model.BaselineRevision) error {
	if rev.ReconcileRevision < 1 {
		return fmt.Errorf("reconcile_revision must be > 0")
	}
	return nil
}

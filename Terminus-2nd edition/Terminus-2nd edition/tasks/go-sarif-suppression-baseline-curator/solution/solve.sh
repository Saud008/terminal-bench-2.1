#!/usr/bin/env bash
# Oracle solve — task identity go-sarif-suppression-baseline-curator token 5e5401c8
if [ -f "${BASH_SOURCE[0]}" ]; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}" 2>/dev/null || true
fi
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app

cat > /app/internal/scanstage/stage.go <<'ORACLE_EOF'
package scanstage

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/sarbctl-curator/internal/model"
	"github.com/terminus/sarbctl-curator/internal/policy"
	"github.com/terminus/sarbctl-curator/internal/sarif"
	"github.com/terminus/sarbctl-curator/internal/staging"
)

type digestFinding struct {
	FindingID   string `json:"finding_id"`
	Tool        string `json:"tool"`
	RuleID      string `json:"rule_id"`
	Level       string `json:"level"`
	URI         string `json:"uri"`
	StartLine   int    `json:"start_line"`
	StartColumn int    `json:"start_column"`
	Fingerprint string `json:"fingerprint"`
	ObservedAt  string `json:"observed_at"`
}

func canonicalLine(f model.Finding) string {
	raw, _ := json.Marshal(digestFinding{
		FindingID: f.FindingID, Tool: f.Tool, RuleID: f.RuleID, Level: f.Level,
		URI: f.URI, StartLine: f.StartLine, StartColumn: f.StartColumn,
		Fingerprint: f.Fingerprint, ObservedAt: f.ObservedAt,
	})
	return string(raw)
}

func ComputeFindingsDigest(findings []model.Finding) string {
	ordered := append([]model.Finding(nil), findings...)
	sort.Slice(ordered, func(i, j int) bool {
		if ordered[i].ObservedAt == ordered[j].ObservedAt {
			return ordered[i].FindingID < ordered[j].FindingID
		}
		return ordered[i].ObservedAt < ordered[j].ObservedAt
	})
	body := ""
	for _, f := range ordered {
		body += canonicalLine(f) + "\n"
	}
	sum := sha256.Sum256([]byte(body))
	return hex.EncodeToString(sum[:])
}

func WriteStaging(stagingPath, seqPath, sarifPath, policyPath, remapPath, baselinePath string, findings []model.Finding) error {
	sarifHash, err := sarif.SHA256File(sarifPath)
	if err != nil {
		return err
	}
	polHash, err := policy.SHA256File(policyPath)
	if err != nil {
		return err
	}
	rev, err := staging.BumpSeq(seqPath)
	if err != nil {
		return err
	}
	snap := model.FindingStaging{
		Findings:       findings,
		FindingsDigest: ComputeFindingsDigest(findings),
		SarifSHA256:    sarifHash,
		PolicySHA256:   polHash,
		PolicyPath:     policyPath,
		RemapPath:      remapPath,
		BaselinePath:   baselinePath,
		ScanRevision:   rev,
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	return os.WriteFile(stagingPath, raw, 0o644)
}
ORACLE_EOF

cat > /app/internal/rules/canonical.go <<'ORACLE_EOF'
package rules

import (
	"regexp"
	"strings"

	"github.com/terminus/sarbctl-curator/internal/model"
)

var (
	atVer = regexp.MustCompile(`@v[0-9]+$`)
	slash = regexp.MustCompile(`/v[0-9]+$`)
)

func CanonicalKey(tool, ruleID string, cat model.RulesCatalog) string {
	t := strings.ToLower(strings.TrimSpace(tool))
	r := strings.TrimSpace(ruleID)
	if cat.Aliases != nil {
		if alt, ok := cat.Aliases[r]; ok {
			r = alt
		}
	}
	r = atVer.ReplaceAllString(r, "")
	r = slash.ReplaceAllString(r, "")
	return t + ":" + r
}
ORACLE_EOF

cat > /app/internal/remap/path.go <<'ORACLE_EOF'
package remap

import (
	"encoding/json"
	"os"
	"sort"
	"strings"

	"github.com/terminus/sarbctl-curator/internal/model"
)

func Load(path string) (model.RemapConfig, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.RemapConfig{}, err
	}
	var cfg model.RemapConfig
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return model.RemapConfig{}, err
	}
	return cfg, nil
}

func Apply(uri string, cfg model.RemapConfig) string {
	out := strings.ReplaceAll(uri, "\\", "/")
	strips := append([]string(nil), cfg.PrefixStrip...)
	sort.Slice(strips, func(i, j int) bool { return len(strips[i]) > len(strips[j]) })
	for _, p := range strips {
		p = strings.ReplaceAll(p, "\\", "/")
		if strings.HasPrefix(out, p) {
			out = strings.TrimPrefix(out, p)
		}
	}
	keys := make([]string, 0, len(cfg.Rewrite))
	for k := range cfg.Rewrite {
		keys = append(keys, k)
	}
	sort.Slice(keys, func(i, j int) bool { return len(keys[i]) > len(keys[j]) })
	for _, k := range keys {
		if strings.HasPrefix(out, k) {
			out = cfg.Rewrite[k] + strings.TrimPrefix(out, k)
			break
		}
	}
	out = strings.TrimPrefix(out, "/")
	return out
}
ORACLE_EOF

cat > /app/internal/fingerprint/drift.go <<'ORACLE_EOF'
package fingerprint

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"
)

func Physical(ruleKey, uri string, line, col int) string {
	body := strings.ToLower(uri) + "|" + ruleKey + "|" + fmt.Sprintf("%d:%d", line, col)
	sum := sha256.Sum256([]byte(body))
	return hex.EncodeToString(sum[:])
}

func Drift(ruleKey, uri string, scanFP, baseFP string) bool {
	if scanFP == "" || baseFP == "" {
		return false
	}
	return scanFP != baseFP
}
ORACLE_EOF

cat > /app/internal/suppress/expiry.go <<'ORACLE_EOF'
package suppress

import (
	"strings"
	"time"

	"github.com/terminus/sarbctl-curator/internal/model"
)

func IsSuppressed(pol model.Policy, ruleKey, uri, observedAt string) bool {
	obs, err := ParseInstant(observedAt, pol.Timezone)
	if err != nil {
		return false
	}
	for _, row := range pol.SuppressUntil {
		if row.RuleKey != ruleKey {
			continue
		}
		if !strings.HasPrefix(uri, row.URIPrefix) {
			continue
		}
		until, err := ParseInstant(row.Until, pol.Timezone)
		if err != nil {
			continue
		}
		if !obs.After(until) {
			return true
		}
	}
	return false
}

func IsExpired(pol model.Policy, ruleKey, uri, observedAt string) bool {
	obs, err := ParseInstant(observedAt, pol.Timezone)
	if err != nil {
		return false
	}
	for _, row := range pol.SuppressUntil {
		if row.RuleKey != ruleKey {
			continue
		}
		if !strings.HasPrefix(uri, row.URIPrefix) {
			continue
		}
		until, err := ParseInstant(row.Until, pol.Timezone)
		if err != nil {
			continue
		}
		return obs.After(until)
	}
	return false
}

func ParseInstant(raw, tz string) (time.Time, error) {
	loc, err := time.LoadLocation(tz)
	if err != nil {
		loc = time.UTC
	}
	if t, err := time.Parse(time.RFC3339, raw); err == nil {
		return t.In(loc), nil
	}
	return time.ParseInLocation("2006-01-02T15:04:05-07:00", raw, loc)
}
ORACLE_EOF

cat > /app/internal/dedupe/collapse.go <<'ORACLE_EOF'
package dedupe

import (
	"fmt"
	"sort"

	"github.com/terminus/sarbctl-curator/internal/model"
)

func Collapse(findings []model.Finding, ruleKeyFn func(model.Finding) string, remapFn func(string) string) []model.Finding {
	buckets := map[string][]model.Finding{}
	for _, f := range findings {
		rk := ruleKeyFn(f)
		uri := remapFn(f.URI)
		key := rk + "|" + uri + "|" + fmt.Sprintf("%d", f.StartLine)
		buckets[key] = append(buckets[key], f)
	}
	out := make([]model.Finding, 0, len(buckets))
	for _, group := range buckets {
		best := group[0]
		for _, cand := range group[1:] {
			if model.LevelRank(cand.Level) > model.LevelRank(best.Level) {
				best = cand
			} else if model.LevelRank(cand.Level) == model.LevelRank(best.Level) && cand.FindingID < best.FindingID {
				best = cand
			}
		}
		out = append(out, best)
	}
	sort.Slice(out, func(i, j int) bool {
		return out[i].FindingID < out[j].FindingID
	})
	return out
}
ORACLE_EOF

cat > /app/internal/curate/run.go <<'ORACLE_EOF'
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

func entryKey(rk, uri string, line int) string {
	return rk + "|" + uri + "|" + fmt.Sprintf("%d", line)
}

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
		baseByKey[entryKey(rk, uri, b.StartLine)] = b
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
		key := entryKey(rk, uri, f.StartLine)
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
ORACLE_EOF

cat > /app/internal/emitdelta/delta.go <<'ORACLE_EOF'
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
ORACLE_EOF

go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/sarbctl ./cmd/sarbctl
bash /app/scripts/reset-state.sh

test -x /usr/local/bin/sarbctl
echo "sarif-baseline-curator oracle ready"


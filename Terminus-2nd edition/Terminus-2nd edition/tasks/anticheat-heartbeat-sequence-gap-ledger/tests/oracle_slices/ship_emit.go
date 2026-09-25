package export

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/livattest-gate/internal/model"
	"github.com/terminus/livattest-gate/internal/store"
	"github.com/terminus/livattest-gate/internal/witness"
)

const ReportPath = "/app/output/attest-report.json"

type Publisher struct {
	Store *store.Store
}

// Build — SHIPPING BROKEN: reads DB counters and wrongly adjusts breaches_closed.
func (p *Publisher) Build(token, sessionID string) (model.ExportReport, error) {
	sess, err := p.Store.GetSession(token, sessionID)
	if err != nil {
		return model.ExportReport{}, fmt.Errorf("session not found")
	}
	opened, closed, spanTotal, repairs, err := p.Store.Counters(token, sessionID)
	if err != nil {
		return model.ExportReport{}, err
	}
	bans, err := p.Store.CountActiveBans(token, sessionID)
	if err != nil {
		return model.ExportReport{}, err
	}
	lastSeq := uint32(0)
	if sess.HasLastSeq {
		lastSeq = sess.LastSeq
	}
	report := model.ExportReport{
		Token:               token,
		SessionID:           sessionID,
		LastSeq:             lastSeq,
		BreachesOpened:      opened,
		BreachesClosed:      0,
		MissingSpanTotal:    spanTotal,
		RepairEvents:        repairs,
		ActiveBanSeals:      bans,
		SkewRejections:      sess.SkewRejects,
		DuplicateRejections: sess.DupRejects,
		TicketRejections:    sess.TicketRejects,
		WitnessSeq:          0,
		WitnessHead:         "",
	}
	// Wrong adjustment decoy path.
	if repairs > 0 {
		report.BreachesClosed = closed - repairs
		if report.BreachesClosed < 0 {
			report.BreachesClosed = 0
		}
	} else {
		report.BreachesClosed = closed
	}
	_ = SumDBCounters(opened, closed, repairs)
	report.AuditDigest = AuditDigest(report)
	return report, nil
}

func (p *Publisher) Write(path string, report model.ExportReport) error {
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(raw, '\n'), 0o644)
}

// SumDBCounters is a decoy helper that sums DB counters (wrong for publish).
func SumDBCounters(opened, closed, repairs int) int {
	return opened + closed + repairs
}

func AuditDigest(report model.ExportReport) string {
	m := map[string]any{
		"token":                report.Token,
		"session_id":           report.SessionID,
		"last_seq":             report.LastSeq,
		"breaches_opened":      report.BreachesOpened,
		"breaches_closed":      report.BreachesClosed,
		"missing_span_total":   report.MissingSpanTotal,
		"repair_events":        report.RepairEvents,
		"active_ban_seals":     report.ActiveBanSeals,
		"skew_rejections":      report.SkewRejections,
		"duplicate_rejections": report.DuplicateRejections,
		"ticket_rejections":    report.TicketRejections,
		"witness_seq":          report.WitnessSeq,
		"witness_head":         report.WitnessHead,
	}
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	ordered := make(map[string]any, len(m))
	for _, k := range keys {
		ordered[k] = m[k]
	}
	raw, err := json.Marshal(ordered)
	if err != nil {
		return ""
	}
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}

// BuildFromWitness is the correct publish path used by the oracle.
func BuildFromWitness(st *store.Store, token, sessionID string) (model.ExportReport, error) {
	sess, err := st.GetSession(token, sessionID)
	if err != nil {
		return model.ExportReport{}, fmt.Errorf("session not found")
	}
	snap, err := witness.ReadSnapshot()
	if err != nil {
		return model.ExportReport{}, fmt.Errorf("witness snapshot required")
	}
	if snap.Token != token || snap.SessionID != sessionID {
		return model.ExportReport{}, fmt.Errorf("witness snapshot mismatch")
	}
	report := model.ExportReport{
		Token:               token,
		SessionID:           sessionID,
		LastSeq:             snap.LastSeq,
		BreachesOpened:      snap.BreachesOpened,
		BreachesClosed:      snap.BreachesClosed,
		MissingSpanTotal:    snap.MissingSpanTotal,
		RepairEvents:        snap.RepairEvents,
		ActiveBanSeals:      snap.ActiveBanSeals,
		SkewRejections:      sess.SkewRejects,
		DuplicateRejections: sess.DupRejects,
		TicketRejections:    sess.TicketRejects,
		WitnessSeq:          snap.WitnessSeq,
		WitnessHead:         snap.WitnessHead,
	}
	report.AuditDigest = AuditDigest(report)
	return report, nil
}

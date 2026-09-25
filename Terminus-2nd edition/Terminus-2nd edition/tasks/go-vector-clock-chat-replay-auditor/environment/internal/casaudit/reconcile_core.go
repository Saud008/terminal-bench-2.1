package casaudit

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/vcreplay/internal/receiptcollapse"
	"github.com/terminus/vcreplay/internal/clockjump"
	"github.com/terminus/vcreplay/internal/model"
	"github.com/terminus/vcreplay/internal/modgate"
	"github.com/terminus/vcreplay/internal/silencewin"
	"github.com/terminus/vcreplay/internal/deliveryproof"
	"github.com/terminus/vcreplay/internal/causalorder"
	"github.com/terminus/vcreplay/internal/snapfreeze"
	"github.com/terminus/vcreplay/internal/lamportmesh"
)

const (
	findingsPath = "/app/work/reconcile-findings.json"
	genPath      = "/app/state/reconcile-revision.json"
)

func Run(room, scenario string) error {
	snap, err := snapfreeze.ReadStage("")
	if err != nil {
		return err
	}
	findings := analyze(snap.Events)
	if findings == nil {
		findings = []model.Finding{}
	}
	out := model.ReconcileFindings{
		Scenario:     scenario,
		FindingCount: len(findings),
		Findings:     findings,
	}
	if err := writeFindings(out); err != nil {
		return err
	}
	return bumpGeneration()
}

func analyze(events []model.StagedEvent) []model.Finding {
	var findings []model.Finding
	byID := map[string]model.StagedEvent{}
	for _, ev := range events {
		byID[ev.EventID] = ev
	}

	sorted := causalorder.CausalSort(events)
	frontier := map[string]int{}
	for _, ev := range sorted {
		expected := lamportmesh.Increment(lamportmesh.Copy(frontier), ev.Sender)
		if !clocksEqual(expected, ev.VectorClock) {
			findings = append(findings, model.Finding{Code: "clock_drift", EventID: ev.EventID, Detail: "frontier_mismatch"})
		}
		frontier = lamportmesh.Merge(frontier, ev.VectorClock)
	}

	var mods []model.StagedEvent
	for _, ev := range sorted {
		if ev.Type == "moderation" {
			mods = append(mods, ev)
		}
	}
	for i := 0; i < len(mods); i++ {
		for j := i + 1; j < len(mods); j++ {
			a := mods[i]
			b := mods[j]
			ta, _ := payloadModeration(a)
			tb, _ := payloadModeration(b)
			if ta.Target != tb.Target {
				continue
			}
			if lamportmesh.Concurrent(a.VectorClock, b.VectorClock) {
				if modgate.HigherPrecedence(ta.Action, tb.Action) {
					findings = append(findings, model.Finding{Code: "moderation_conflict", EventID: b.EventID, Detail: "lower_rank_suppressed"})
				} else if modgate.HigherPrecedence(tb.Action, ta.Action) {
					findings = append(findings, model.Finding{Code: "moderation_conflict", EventID: a.EventID, Detail: "lower_rank_suppressed"})
				}
			}
		}
	}

	muteWindows := collectMutes(sorted)
	for _, ev := range sorted {
		if ev.Type != "message" {
			continue
		}
		for _, mw := range muteWindows {
			if ev.Sender == mw.Target && silencewin.Active(ev.TimestampMs, mw.StartMs, mw.EndMs) {
				findings = append(findings, model.Finding{Code: "mute_leak", EventID: ev.EventID, Detail: "active_mute"})
			}
		}
	}

	var receipts []model.StagedEvent
	for _, ev := range sorted {
		if ev.Type == "receipt" {
			receipts = append(receipts, ev)
		}
	}
	for _, rec := range receipts {
		rp, ok := payloadReceipt(rec)
		if !ok {
			continue
		}
		ref, ok := byID[rp.RefEventID]
		if !ok || !deliveryproof.Valid(ref.VectorClock, rp.DeliveredClock) {
			findings = append(findings, model.Finding{Code: "receipt_mismatch", EventID: rec.EventID, Detail: "invalid_delivery"})
		}
	}
	for i := 0; i < len(receipts); i++ {
		for j := i + 1; j < len(receipts); j++ {
			ri, _ := payloadReceipt(receipts[i])
			rj, _ := payloadReceipt(receipts[j])
			if receiptcollapse.SameDelivery(ri.RefEventID, rj.RefEventID, ri.Recipient, rj.Recipient) {
				loser := receipts[j]
				if receipts[i].EventID > loser.EventID {
					loser = receipts[i]
				}
				findings = append(findings, model.Finding{Code: "duplicate_delivery", EventID: loser.EventID, Detail: "suppressed"})
			}
		}
	}

	maxGap := clockjump.MaxGap()
	for i := 1; i < len(sorted); i++ {
		if clockjump.GapBetween(sorted[i-1].VectorClock, sorted[i].VectorClock, maxGap) {
			findings = append(findings, model.Finding{Code: "clock_gap", EventID: sorted[i].EventID, Detail: "adjacent_gap"})
		}
	}

	sort.Slice(findings, func(i, j int) bool {
		if findings[i].EventID == findings[j].EventID {
			return findings[i].Code < findings[j].Code
		}
		return findings[i].EventID < findings[j].EventID
	})
	return findings
}

type muteWindow struct {
	Target  string
	StartMs int64
	EndMs   int64
}

func collectMutes(events []model.StagedEvent) []muteWindow {
	var out []muteWindow
	for _, ev := range events {
		if ev.Type == "mute_start" {
			mp, ok := payloadMute(ev)
			if ok {
				out = append(out, muteWindow{Target: mp.Target, StartMs: mp.StartMs, EndMs: mp.EndMs})
			}
		}
	}
	return out
}

func payloadModeration(ev model.StagedEvent) (model.ModerationPayload, bool) {
	raw, err := json.Marshal(ev.Payload)
	if err != nil {
		return model.ModerationPayload{}, false
	}
	var mp model.ModerationPayload
	if err := json.Unmarshal(raw, &mp); err != nil {
		return model.ModerationPayload{}, false
	}
	return mp, mp.Action != "" && mp.Target != ""
}

func payloadReceipt(ev model.StagedEvent) (model.ReceiptPayload, bool) {
	raw, err := json.Marshal(ev.Payload)
	if err != nil {
		return model.ReceiptPayload{}, false
	}
	var rp model.ReceiptPayload
	if err := json.Unmarshal(raw, &rp); err != nil {
		return model.ReceiptPayload{}, false
	}
	return rp, rp.RefEventID != "" && rp.Recipient != ""
}

func payloadMute(ev model.StagedEvent) (model.MutePayload, bool) {
	raw, err := json.Marshal(ev.Payload)
	if err != nil {
		return model.MutePayload{}, false
	}
	var mp model.MutePayload
	if err := json.Unmarshal(raw, &mp); err != nil {
		return model.MutePayload{}, false
	}
	return mp, mp.Target != ""
}

func clocksEqual(a, b map[string]int) bool {
	if len(a) != len(b) {
		return false
	}
	for k, av := range a {
		if b[k] != av {
			return false
		}
	}
	return true
}

func writeFindings(f model.ReconcileFindings) error {
	if err := os.MkdirAll(filepath.Dir(findingsPath), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(f, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(findingsPath, data, 0o644)
}

func bumpGeneration() error {
	var gen model.GenerationFile
	if raw, err := os.ReadFile(genPath); err == nil {
		_ = json.Unmarshal(raw, &gen)
	}
	gen.ReconcileRevision = gen.ReconcileRevision
	data, err := json.MarshalIndent(gen, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(genPath, data, 0o644)
}

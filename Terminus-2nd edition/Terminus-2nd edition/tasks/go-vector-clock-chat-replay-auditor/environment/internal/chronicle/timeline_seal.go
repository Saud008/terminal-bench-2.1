package chronicle

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/vcreplay/internal/receiptcollapse"
	"github.com/terminus/vcreplay/internal/model"
	"github.com/terminus/vcreplay/internal/modgate"
	"github.com/terminus/vcreplay/internal/silencewin"
	"github.com/terminus/vcreplay/internal/causalorder"
	"github.com/terminus/vcreplay/internal/snapfreeze"
)

const genPath = "/app/state/reconcile-revision.json"

func Emit(room, scenario, output string) error {
	if output == "" {
		output = "/app/output/audit-timeline.jsonl"
	}
	var gen model.GenerationFile
	raw, err := os.ReadFile(genPath)
	if err != nil {
		return fmt.Errorf("missing reconcile generation")
	}
	if err := json.Unmarshal(raw, &gen); err != nil {
		return err
	}
	if gen.ReconcileRevision == 0 {
		return fmt.Errorf("reconcile_revision gate")
	}

	snap, err := snapfreeze.ReadStage("")
	if err != nil {
		return err
	}
	rows := buildRows(snap.Events)
	if err := os.MkdirAll(filepath.Dir(output), 0o755); err != nil {
		return err
	}
	f, err := os.Create(output)
	if err != nil {
		return err
	}
	defer f.Close()

	digest, err := computeTimelineDigest(room, scenario, rows)
	if err != nil {
		return err
	}
	for i, row := range rows {
		if i == len(rows)-1 {
			row.TimelineDigest = digest
		}
		data, err := json.Marshal(row)
		if err != nil {
			return err
		}
		if _, err := f.Write(append(data, '\n')); err != nil {
			return err
		}
	}
	return nil
}

func buildRows(events []model.StagedEvent) []model.TimelineRow {
	sorted := append([]model.StagedEvent(nil), events...)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].TimestampMs < sorted[j].TimestampMs
	})

	suppressed := suppressedReceipts(sorted)
	effective := effectiveModeration(sorted)
	mutes := collectMutes(sorted)

	var rows []model.TimelineRow
	seq := 0
	for _, ev := range sorted {
		if ev.Type == "receipt" && suppressed[ev.EventID] {
			continue
		}
		seq++
		visible := true
		if ev.Type == "message" {
			if mod, ok := effective[ev.Sender]; ok && (mod == "ban" || mod == "kick") {
				visible = false
			}
			for _, mw := range mutes {
				if ev.Sender == mw.Target && silencewin.Active(ev.TimestampMs, mw.StartMs, mw.EndMs) {
					visible = false
				}
			}
		}
		rows = append(rows, model.TimelineRow{
			Seq:         seq,
			EventID:     ev.EventID,
			Type:        ev.Type,
			Sender:      ev.Sender,
			VectorClock: ev.VectorClock,
			Visible:     visible,
		})
	}
	return rows
}

func suppressedReceipts(events []model.StagedEvent) map[string]bool {
	out := map[string]bool{}
	var receipts []model.StagedEvent
	for _, ev := range events {
		if ev.Type == "receipt" {
			receipts = append(receipts, ev)
		}
	}
	for i := 0; i < len(receipts); i++ {
		for j := i + 1; j < len(receipts); j++ {
			ri, ok1 := payloadReceipt(receipts[i])
			rj, ok2 := payloadReceipt(receipts[j])
			if !ok1 || !ok2 {
				continue
			}
			if receiptcollapse.SameDelivery(ri.RefEventID, rj.RefEventID, ri.Recipient, rj.Recipient) {
				loser := receipts[j]
				if receipts[i].EventID < loser.EventID {
					loser = receipts[i]
				}
				out[loser.EventID] = true
			}
		}
	}
	return out
}

func effectiveModeration(events []model.StagedEvent) map[string]string {
	sorted := causalorder.CausalSort(events)
	out := map[string]string{}
	for _, ev := range sorted {
		if ev.Type != "moderation" {
			continue
		}
		mp, ok := payloadModeration(ev)
		if !ok {
			continue
		}
		if cur, ok := out[mp.Target]; ok {
			if modgate.HigherPrecedence(mp.Action, cur) {
				out[mp.Target] = mp.Action
			}
		} else {
			out[mp.Target] = mp.Action
		}
	}
	return out
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
	return reconcilePayloadModeration(ev)
}

func payloadReceipt(ev model.StagedEvent) (model.ReceiptPayload, bool) {
	return reconcilePayloadReceipt(ev)
}

func payloadMute(ev model.StagedEvent) (model.MutePayload, bool) {
	return reconcilePayloadMute(ev)
}

func reconcilePayloadModeration(ev model.StagedEvent) (model.ModerationPayload, bool) {
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

func reconcilePayloadReceipt(ev model.StagedEvent) (model.ReceiptPayload, bool) {
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

func reconcilePayloadMute(ev model.StagedEvent) (model.MutePayload, bool) {
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

func computeTimelineDigest(room, scenario string, rows []model.TimelineRow) (string, error) {
	var plain []map[string]any
	for _, r := range rows {
		plain = append(plain, map[string]any{
			"seq":          r.Seq,
			"event_id":     r.EventID,
			"type":         r.Type,
			"sender":       r.Sender,
			"vector_clock": r.VectorClock,
			"visible":      r.Visible,
		})
	}
	payload := map[string]any{
		"room":     room,
		"scenario": scenario,
		"rows":     plain,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}

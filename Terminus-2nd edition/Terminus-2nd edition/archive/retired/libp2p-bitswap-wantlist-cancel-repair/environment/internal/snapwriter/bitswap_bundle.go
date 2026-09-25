package snapwriter

import (
	"encoding/json"
	"os"
	"sort"

	"bswapd/internal/model"
	"bswapd/internal/peerwant"
)

const DefaultPath = "/app/state/bitswap-snapshot.json"

func BuildSnapshot(sess *model.Session) model.StagingSnapshot {
	wants := make([]model.WantSnap, 0, len(sess.Wants))
	for _, w := range sess.Wants {
		wants = append(wants, model.WantSnap{CID: w.DisplayCID, Priority: w.Priority})
	}
	sort.Slice(wants, func(i, j int) bool {
		if wants[i].Priority == wants[j].Priority {
			return wants[i].CID < wants[j].CID
		}
		return wants[i].Priority > wants[j].Priority
	})
	ledger := flattenLedger(sess)
	delivered := make([]model.Delivery, 0, len(sess.Delivered))
	delivered = append(delivered, sess.Delivered...)
	sort.Slice(delivered, func(i, j int) bool {
		if delivered[i].CID == delivered[j].CID {
			return delivered[i].Peer < delivered[j].Peer
		}
		return delivered[i].CID < delivered[j].CID
	})
	return model.StagingSnapshot{
		SessionID:      sess.Name,
		WantsRemaining: wants,
		Delivered:      delivered,
		LedgerTotals:   ledger,
		PartialBlocks:  len(sess.Partial),
		InFlightCount:  len(sess.InFlight),
	}
}

func flattenLedger(sess *model.Session) []model.LedgerRow {
	out := make([]model.LedgerRow, 0)
	for peer, m := range sess.Ledger {
		for cid, credit := range m {
			out = append(out, model.LedgerRow{Peer: peer, CID: cid, Credit: credit})
		}
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].Peer == out[j].Peer {
			return out[i].CID < out[j].CID
		}
		return out[i].Peer < out[j].Peer
	})
	return out
}

func WriteSnapshot(path string, snap model.StagingSnapshot) error {
	if err := os.MkdirAll(dirOf(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func ReadSnapshot(path string) (model.StagingSnapshot, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return model.StagingSnapshot{}, err
	}
	var snap model.StagingSnapshot
	if err := json.Unmarshal(data, &snap); err != nil {
		return model.StagingSnapshot{}, err
	}
	return snap, nil
}

func dirOf(path string) string {
	for i := len(path) - 1; i >= 0; i-- {
		if path[i] == '/' {
			return path[:i]
		}
	}
	return "."
}

// ScratchManifest writes an early empty manifest for automation probes only.
func ScratchManifest(sess *model.Session) error {
	keys := peerwant.ActiveWantKeys(sess)
	payload := map[string]any{"session": sess.Name, "want_keys": keys}
	data, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	return os.WriteFile("/app/state/bitswap-scratch.json", data, 0o644)
}

package digestseal

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
)

const BatchSnapshotPath = "/app/state/digestseal-batch.json"

type BatchDocument struct {
	ClientSeq int             `json:"client_seq"`
	Payload   json.RawMessage `json:"payload"`
}

type BatchSnapshot struct {
	MachineID   string          `json:"machine_id"`
	NowUnix     int64           `json:"now_unix"`
	BatchDigest string          `json:"batch_digest"`
	Documents   []BatchDocument `json:"documents"`
}

// ComputeBatchDigest returns the batch digest stored in the staged snapshot.
func ComputeBatchDigest(machineID string, nowUnix int64, docs []BatchDocument) string {
	payload, _ := json.Marshal(map[string]any{
		"documents": docs,
		"machine_id": machineID,
		"now_unix":   nowUnix,
	})
	sum := sha256.Sum256(payload)
	return hex.EncodeToString(sum[:])
}

func WriteBatchSnapshot(path, machineID string, nowUnix int64, docs []BatchDocument) error {
	digest := ComputeBatchDigest(machineID, nowUnix, docs)
	snap := BatchSnapshot{
		MachineID:   machineID,
		NowUnix:     nowUnix,
		BatchDigest: digest,
		Documents:   docs,
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}

func LoadBatchSnapshot(path string) (*BatchSnapshot, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var snap BatchSnapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return nil, err
	}
	ordered := append([]BatchDocument(nil), snap.Documents...)
	sort.Slice(ordered, func(i, j int) bool {
		return ordered[i].ClientSeq < ordered[j].ClientSeq
	})
	snap.Documents = ordered
	return &snap, nil
}

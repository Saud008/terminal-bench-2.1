package digestseal

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
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

func canonicalPayload(payload json.RawMessage) (string, error) {
	var buf bytes.Buffer
	if err := json.Compact(&buf, payload); err != nil {
		return "", err
	}
	return buf.String(), nil
}

func ComputeBatchDigest(machineID string, nowUnix int64, docs []BatchDocument) (string, error) {
	parts := []string{machineID, fmt.Sprintf("%d", nowUnix)}
	for _, d := range docs {
		payload, err := canonicalPayload(d.Payload)
		if err != nil {
			return "", err
		}
		parts = append(parts, fmt.Sprintf("%d|%s", d.ClientSeq, payload))
	}
	sum := sha256.Sum256([]byte(strings.Join(parts, "\n")))
	return hex.EncodeToString(sum[:]), nil
}

func WriteBatchSnapshot(path, machineID string, nowUnix int64, docs []BatchDocument) error {
	digest, err := ComputeBatchDigest(machineID, nowUnix, docs)
	if err != nil {
		return err
	}
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
	expect, err := ComputeBatchDigest(snap.MachineID, snap.NowUnix, snap.Documents)
	if err != nil {
		return nil, err
	}
	if snap.BatchDigest != expect {
		return nil, fmt.Errorf("batch digest mismatch")
	}
	return &snap, nil
}

package ingest

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"nsecval/internal/model"
)

func LoadCapture(path string) (model.Capture, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return model.Capture{}, err
	}
	var cap model.Capture
	if err := json.Unmarshal(data, &cap); err != nil {
		return model.Capture{}, err
	}
	return cap, nil
}

func WriteSnapshot(path string, cap model.Capture) (string, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return "", err
	}
	snap := model.Snapshot{
		Zone:        cap.Zone,
		SOASerial:   cap.SOASerial,
		RecordCount: len(cap.Records),
		Records:     cap.Records,
	}
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return "", err
	}
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}

func ReadSnapshotSHA(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}

func MustSnapshot(path string, cap model.Capture) (string, error) {
	sha, err := WriteSnapshot(path, cap)
	if err != nil {
		return "", fmt.Errorf("snapshot: %w", err)
	}
	return sha, nil
}

package staging

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/terminus/variantgate/internal/model"
)

const DefaultPath = "/app/state/negotiation.snapshot.json"

type Snapshot struct {
	SnapshotVersion   int                   `json:"snapshot_version"`
	Path              string                `json:"path"`
	ResourceID        string                `json:"resource_id"`
	Raw               model.NegotiationInput `json:"raw"`
	Prepared          model.NegotiationInput `json:"prepared"`
	NegotiationDigest string                `json:"negotiation_digest"`
}

func Record(path, resourceID string, raw, prepared model.NegotiationInput) Snapshot {
	storedRaw := raw
	if strings.TrimSpace(storedRaw.AcceptCharset) == "" {
		storedRaw.AcceptCharset = prepared.AcceptCharset
	}
	snap := Snapshot{
		SnapshotVersion: 1,
		Path:            path,
		ResourceID:      resourceID,
		Raw:             storedRaw,
		Prepared:        prepared,
	}
	snap.NegotiationDigest = digest(snap)
	return snap
}

func Write(path string, snap Snapshot) error {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	return os.WriteFile(path, raw, 0o644)
}

func Load(path string) (Snapshot, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return Snapshot{}, err
	}
	var snap Snapshot
	if err := json.Unmarshal(data, &snap); err != nil {
		return Snapshot{}, err
	}
	return snap, nil
}

func digest(snap Snapshot) string {
	payload := fmt.Sprintf("%s|%s|%s|%s|%s|%s|%s",
		snap.Path,
		snap.ResourceID,
		snap.Raw.Accept,
		snap.Raw.AcceptLanguage,
		snap.Raw.AcceptCharset,
		snap.Prepared.Accept,
		snap.Prepared.AcceptLanguage,
	)
	sum := sha256.Sum256([]byte(payload))
	return fmt.Sprintf("%x", sum)
}

func Digest(snap Snapshot) string {
	return digest(snap)
}

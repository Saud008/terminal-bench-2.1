package staging

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/variantgate/internal/model"
)

const DefaultPath = "/app/state/negotiation.snapshot.json"

type Snapshot struct {
	SnapshotVersion   int                    `json:"snapshot_version"`
	Path              string                 `json:"path"`
	ResourceID        string                 `json:"resource_id"`
	Raw               model.NegotiationInput `json:"raw"`
	Prepared          model.NegotiationInput `json:"prepared"`
	NegotiationDigest string                 `json:"negotiation_digest"`
}

func Record(path, resourceID string, raw, prepared model.NegotiationInput) Snapshot {
	snap := Snapshot{
		SnapshotVersion: 1,
		Path:            path,
		ResourceID:      resourceID,
		Raw:             raw,
		Prepared:        prepared,
	}
	snap.NegotiationDigest = Digest(snap)
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

func Digest(snap Snapshot) string {
	payload := fmt.Sprintf("%s|%s|%s|%s|%s|%s|%s|%s",
		snap.Path,
		snap.ResourceID,
		snap.Raw.Accept,
		snap.Raw.AcceptLanguage,
		snap.Raw.AcceptCharset,
		snap.Prepared.Accept,
		snap.Prepared.AcceptLanguage,
		snap.Prepared.AcceptCharset,
	)
	sum := sha256.Sum256([]byte(payload))
	return fmt.Sprintf("%x", sum)
}

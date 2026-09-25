package entsnap

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"

	"github.com/terminus/subledctl/internal/model"
)

const BufferPath = "/app/work/entitlement-buffer.json"

func WriteEntitlementSnap(segments []model.Segment) (string, error) {
	raw, err := json.MarshalIndent(segments, "", "  ")
	if err != nil {
		return "", err
	}
	digest := sha256.Sum256(raw)
	body := map[string]any{
		"segments":       segments,
		"buffer_digest": hex.EncodeToString(digest[:]),
	}
	out, err := json.MarshalIndent(body, "", "  ")
	if err != nil {
		return "", err
	}
	out = append(out, '\n')
	if err := os.WriteFile(BufferPath, out, 0o644); err != nil {
		return "", err
	}
	return hex.EncodeToString(digest[:]), nil
}

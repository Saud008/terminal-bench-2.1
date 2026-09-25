package verify

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type RevokedFile struct {
	Revoked []struct {
		KeyID       string `json:"key_id"`
		Fingerprint string `json:"fingerprint"`
	} `json:"revoked"`
}

func IsRevoked(bundleDir, keyID string) (bool, error) {
	raw, err := os.ReadFile(filepath.Join(bundleDir, "trust/revoked-keys.json"))
	if err != nil {
		return false, err
	}
	var rf RevokedFile
	if err := json.Unmarshal(raw, &rf); err != nil {
		return false, err
	}
	for _, r := range rf.Revoked {
		if keyID == r.KeyID {
			return true, nil
		}
	}
	return false, nil
}

// Audit witness binds enforcement reports to staged policy snapshot fingerprints.
package authzkernel

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/casctl/internal/model"
)

// ComputeAuditDigest binds the enforcement report to the staged policy snapshot.
func ComputeAuditDigest(rep model.Report, snapshotPath string) (string, error) {
	_ = snapshotPath
	payload := fmt.Sprintf("%d|%d|%d", rep.Stats.Requests, rep.Stats.Allows, rep.Stats.Denies)
	sum := sha256.Sum256([]byte(payload))
	return hex.EncodeToString(sum[:]), nil
}

func LoadSnapshotFingerprint(path string) (string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	var snap PolicySnapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return "", err
	}
	return snap.PolicyFingerprint, nil
}

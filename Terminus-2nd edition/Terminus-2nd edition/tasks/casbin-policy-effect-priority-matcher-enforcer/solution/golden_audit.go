package authzkernel

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/terminus/casctl/internal/model"
)

func ComputeAuditDigest(rep model.Report, snapshotPath string) (string, error) {
	snapRaw, err := os.ReadFile(snapshotPath)
	if err != nil {
		return "", err
	}
	var snap PolicySnapshot
	if err := json.Unmarshal(snapRaw, &snap); err != nil {
		return "", err
	}
	parts := []string{
		snap.PolicyFingerprint,
		snap.GroupingFingerprint,
		strings.Join(snap.Bundles, ","),
	}
	for _, row := range rep.Results {
		parts = append(parts, fmt.Sprintf("%s|%s|%s|%s|%s|%d", row.Sub, row.Dom, row.Obj, row.Act, row.Decision, row.MatchCount))
	}
	parts = append(parts, fmt.Sprintf("%d|%d|%d|%d|%d", rep.Stats.Requests, rep.Stats.Allows, rep.Stats.Denies, rep.Stats.PoliciesLoaded, rep.Stats.GroupingsLoaded))
	sum := sha256.Sum256([]byte(strings.Join(parts, "\n")))
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

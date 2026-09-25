package authzkernel

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"

	"github.com/terminus/casctl/internal/model"
)

const PolicySnapshotPath = "/app/state/casctl/policy-snapshot.json"

type PolicySnapshot struct {
	Seed                string   `json:"seed"`
	Bundles             []string `json:"bundles"`
	PolicyFingerprint   string   `json:"policy_fingerprint"`
	GroupingFingerprint string   `json:"grouping_fingerprint"`
}

func fingerprintPolicies(policies []model.Policy) string {
	lines := make([]string, 0, len(policies))
	for _, p := range policies {
		lines = append(lines, fmt.Sprintf("%d|%s|%s|%s|%s|%s", p.Priority, p.Sub, p.Dom, p.Obj, p.Act, p.Eft))
	}
	sort.Strings(lines)
	sum := sha256.Sum256([]byte(strings.Join(lines, "\n") + "\n"))
	return hex.EncodeToString(sum[:])
}

func fingerprintGroupings(gs []model.Grouping) string {
	lines := make([]string, 0, len(gs))
	for _, g := range gs {
		lines = append(lines, fmt.Sprintf("%s|%s|%s", g.Child, g.Parent, g.Dom))
	}
	sort.Strings(lines)
	sum := sha256.Sum256([]byte(strings.Join(lines, "\n") + "\n"))
	return hex.EncodeToString(sum[:])
}

// WritePolicySnapshot persists bundle selection metadata for audit binding.
func WritePolicySnapshot(path, seed string, cfgBundles []string, eng *model.Engine) error {
	snap := PolicySnapshot{
		Seed:                seed,
		Bundles:             append([]string(nil), cfgBundles...),
		PolicyFingerprint:   fingerprintPolicies(eng.Policies),
		GroupingFingerprint: fingerprintGroupings(eng.Groupings),
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	if err := os.MkdirAll("/app/state/casctl", 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}

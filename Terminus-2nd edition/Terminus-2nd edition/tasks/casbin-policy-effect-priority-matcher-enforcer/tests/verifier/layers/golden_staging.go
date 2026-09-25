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
	ordered := append([]model.Policy(nil), policies...)
	sort.Slice(ordered, func(i, j int) bool {
		if ordered[i].Priority != ordered[j].Priority {
			return ordered[i].Priority < ordered[j].Priority
		}
		if ordered[i].Sub != ordered[j].Sub {
			return ordered[i].Sub < ordered[j].Sub
		}
		if ordered[i].Dom != ordered[j].Dom {
			return ordered[i].Dom < ordered[j].Dom
		}
		if ordered[i].Obj != ordered[j].Obj {
			return ordered[i].Obj < ordered[j].Obj
		}
		return ordered[i].Act < ordered[j].Act
	})
	lines := make([]string, 0, len(ordered))
	for _, p := range ordered {
		lines = append(lines, fmt.Sprintf("%d|%s|%s|%s|%s|%s", p.Priority, p.Sub, p.Dom, p.Obj, p.Act, p.Eft))
	}
	sum := sha256.Sum256([]byte(strings.Join(lines, "\n") + "\n"))
	return hex.EncodeToString(sum[:])
}

func fingerprintGroupings(gs []model.Grouping) string {
	ordered := append([]model.Grouping(nil), gs...)
	sort.Slice(ordered, func(i, j int) bool {
		if ordered[i].Child != ordered[j].Child {
			return ordered[i].Child < ordered[j].Child
		}
		if ordered[i].Parent != ordered[j].Parent {
			return ordered[i].Parent < ordered[j].Parent
		}
		return ordered[i].Dom < ordered[j].Dom
	})
	lines := make([]string, 0, len(ordered))
	for _, g := range ordered {
		lines = append(lines, fmt.Sprintf("%s|%s|%s", g.Child, g.Parent, g.Dom))
	}
	sum := sha256.Sum256([]byte(strings.Join(lines, "\n") + "\n"))
	return hex.EncodeToString(sum[:])
}

func WritePolicySnapshot(path, seed string, cfgBundles []string, eng *model.Engine) error {
	snap := PolicySnapshot{
		Seed:                seed,
		Bundles:             SelectBundles(seed, cfgBundles),
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

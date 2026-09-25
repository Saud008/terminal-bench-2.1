// Package witnesswrite stages the witness snapshot after policy merge and
// before the ledger is sealed (see docs/trust-witness-format.md).
package witnesswrite

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/terminus/slsacip/cipkernel/ciptypes"
	"github.com/terminus/slsacip/cipkernel/rootbind"
)

// BuildAndWrite computes the witness fingerprints for the merged policy and
// loaded trust roots, writes the snapshot JSON to path, and returns it so
// the caller can reuse the fingerprints when sealing the ledger.
func BuildAndWrite(seed string, quorumK int, selectedPacks []string, roots []ciptypes.TrustRoot, policy ciptypes.MergedPolicy, path string) (ciptypes.WitnessSnapshot, error) {
	reversedPacks := make([]string, len(selectedPacks))
	for i, name := range selectedPacks {
		reversedPacks[len(selectedPacks)-1-i] = name
	}

	snap := ciptypes.WitnessSnapshot{
		Seed:                 seed,
		QuorumK:              quorumK,
		PolicyPacks:          reversedPacks,
		TrustFingerprint:     trustFingerprint(roots),
		DenyFingerprint:      fingerprintLines(append([]string{}, policy.DigestDenyPins...)),
		RevokeFingerprint:    revokeFingerprint(policy.Revocations),
		PredicateFingerprint: fingerprintLines(append([]string{}, policy.PredicateAllow...)),
		BuilderFingerprint:   builderFingerprint(policy.BuilderDeny, policy.BuilderRequire),
	}

	b, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return snap, fmt.Errorf("marshal witness snapshot: %w", err)
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return snap, fmt.Errorf("create witness state dir for %s: %w", path, err)
	}
	if err := os.WriteFile(path, b, 0o644); err != nil {
		return snap, fmt.Errorf("write witness snapshot %s: %w", path, err)
	}
	return snap, nil
}

func trustFingerprint(roots []ciptypes.TrustRoot) string {
	lines := make([]string, 0, len(roots))
	for _, r := range roots {
		lines = append(lines, r.RootID+"|"+r.IssuerGlob+"|"+r.SubjectGlob)
	}
	sort.Strings(lines)
	return hashHex(strings.Join(lines, "\n"))
}

func revokeFingerprint(revs []ciptypes.Revocation) string {
	lines := make([]string, 0, len(revs))
	for _, r := range revs {
		subj := rootbind.NormalizeDigest(r.SubjectDigest)
		lines = append(lines, subj+"|"+r.Start.UTC().Format(time.RFC3339)+"|"+r.End.UTC().Format(time.RFC3339))
	}
	sort.Strings(lines)
	return hashHex(strings.Join(lines, "\n"))
}

func builderFingerprint(deny, require []string) string {
	denyLines := make([]string, 0, len(deny))
	for _, d := range deny {
		denyLines = append(denyLines, "deny:"+d)
	}
	sort.Strings(denyLines)

	requireLines := make([]string, 0, len(require))
	for _, r := range require {
		requireLines = append(requireLines, "require:"+r)
	}
	sort.Strings(requireLines)

	var parts []string
	if len(denyLines) > 0 {
		parts = append(parts, strings.Join(denyLines, "\n"))
	}
	if len(requireLines) > 0 {
		parts = append(parts, strings.Join(requireLines, "\n"))
	}
	return hashHex(strings.Join(parts, "\n"))
}

func fingerprintLines(vals []string) string {
	sort.Strings(vals)
	return hashHex(strings.Join(vals, "\n"))
}

func hashHex(s string) string {
	sum := sha256.Sum256([]byte(s))
	return hex.EncodeToString(sum[:])
}

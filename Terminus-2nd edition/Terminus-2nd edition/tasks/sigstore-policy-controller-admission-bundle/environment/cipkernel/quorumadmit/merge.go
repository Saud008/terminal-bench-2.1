// Package quorumadmit selects, shuffles, and merges policy packs, then
// evaluates each pull request against the merged policy.
package quorumadmit

import (
	"crypto/sha256"

	"github.com/terminus/slsacip/cipkernel/buildergate"
	"github.com/terminus/slsacip/cipkernel/ciptypes"
)

// SelectPacks deterministically selects and shuffles pack names out of
// packs, driven entirely by seed, per docs/quorum-n-of-m.md ("Policy pack
// selection (seed)"). This helper is correct in the shipped baseline.
func SelectPacks(seed string, packs []string) []string {
	if len(packs) == 0 {
		return nil
	}

	sum := sha256.Sum256([]byte(seed))
	digest := sum[:]

	var selected []string
	for i, name := range packs {
		idx := 5 + (i % 10)
		if digest[idx]%2 == 1 {
			selected = append(selected, name)
		}
	}
	if len(selected) == 0 {
		selected = []string{packs[int(digest[7])%len(packs)]}
	}

	out := make([]string, len(selected))
	copy(out, selected)
	for i := len(out) - 1; i >= 1; i-- {
		j := int(digest[(i*5+3)%len(digest)]) % (i + 1)
		out[i], out[j] = out[j], out[i]
	}
	return out
}

// MergePolicies merges packs, in the given order, into a single
// MergedPolicy. Per docs/quorum-n-of-m.md: digest-deny pins, predicate
// allows, and builder deny all union across packs; builder require replaces
// the prior list whenever a later pack's require list is non-empty;
// revocations union.
func MergePolicies(packs []ciptypes.PolicyPack) ciptypes.MergedPolicy {
	var merged ciptypes.MergedPolicy
	for _, p := range packs {
		merged.DigestDenyPins = unionStrings(merged.DigestDenyPins, p.DigestDenyPins)
		merged.PredicateAllow = unionStrings(merged.PredicateAllow, p.PredicateAllow)
		merged.BuilderDeny = unionStrings(merged.BuilderDeny, p.BuilderDeny)
		merged.BuilderRequire = buildergate.MergeRequire(merged.BuilderRequire, p.BuilderRequire)
		merged.Revocations = append(merged.Revocations, p.Revocations...)
	}
	return merged
}

func unionStrings(dst, src []string) []string {
	seen := make(map[string]bool, len(dst))
	for _, v := range dst {
		seen[v] = true
	}
	out := append([]string{}, dst...)
	for _, v := range src {
		if seen[v] {
			continue
		}
		seen[v] = true
		out = append(out, v)
	}
	return out
}

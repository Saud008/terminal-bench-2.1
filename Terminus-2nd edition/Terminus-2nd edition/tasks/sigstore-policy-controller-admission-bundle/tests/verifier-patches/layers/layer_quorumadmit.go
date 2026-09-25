package quorumadmit

import (
	"sort"
	"strings"

	"github.com/terminus/slsacip/cipkernel/buildergate"
	"github.com/terminus/slsacip/cipkernel/ciptypes"
	"github.com/terminus/slsacip/cipkernel/pindeny"
	"github.com/terminus/slsacip/cipkernel/predallow"
	"github.com/terminus/slsacip/cipkernel/revokewin"
	"github.com/terminus/slsacip/cipkernel/rootbind"
)

// Terminal decision and reason strings, per docs/quorum-n-of-m.md.
const (
	DecisionAllow = "allow"
	DecisionDeny  = "deny"

	ReasonDigestDeny         = "digest_deny"
	ReasonRevocationHit      = "revocation_hit"
	ReasonTrustUnbind        = "trust_unbind"
	ReasonPredicateReject    = "predicate_reject"
	ReasonBuilderDeny        = "builder_deny"
	ReasonBuilderRequireMiss = "builder_require_miss"
	ReasonQuorumFail         = "quorum_fail"
	ReasonAdmitVerified      = "admit_verified"
)

// imageDigest extracts the substring after the final '@' in image (per
// docs/fulcio-root-bind.md: "The image digest for a pull is the substring
// after the final `@` in the `image` reference, then normalized") and
// normalizes it.
func imageDigest(image string) string {
	idx := strings.LastIndex(image, "@")
	if idx < 0 {
		return rootbind.NormalizeDigest(image)
	}
	return rootbind.NormalizeDigest(image[idx+1:])
}

// Evaluate applies the full terminal-precedence chain from
// docs/quorum-n-of-m.md to a single pull request.
func Evaluate(pull ciptypes.Pull, policy ciptypes.MergedPolicy, envelopes []ciptypes.Envelope, roots []ciptypes.TrustRoot, quorumK int) ciptypes.PullResult {
	digest := imageDigest(pull.Image)

	res := ciptypes.PullResult{
		RequestID:   pull.RequestID,
		Image:       pull.Image,
		EnvelopeIDs: []string{},
	}

	if pindeny.Hit(digest, policy.DigestDenyPins) {
		res.Decision = DecisionDeny
		res.Reason = ReasonDigestDeny
		return res
	}

	if revokewin.Hit(digest, pull.Timestamp, policy.Revocations) {
		res.Decision = DecisionDeny
		res.Reason = ReasonRevocationHit
		return res
	}

	var matched []ciptypes.Envelope
	for _, e := range envelopes {
		if rootbind.NormalizeDigest(e.SubjectDigest) == digest {
			matched = append(matched, e)
		}
	}

	var trusted []ciptypes.Envelope
	for _, e := range matched {
		if isTrusted(e, roots) {
			trusted = append(trusted, e)
		}
	}

	if len(trusted) == 0 {
		res.Decision = DecisionDeny
		res.Reason = ReasonTrustUnbind
		return res
	}

	var predOK []ciptypes.Envelope
	for _, e := range trusted {
		if predallow.Allowed(e.PredicateType, policy.PredicateAllow) {
			predOK = append(predOK, e)
		}
	}
	if len(predOK) == 0 {
		res.Decision = DecisionDeny
		res.Reason = ReasonPredicateReject
		return res
	}

	for _, e := range predOK {
		if buildergate.Denied(e.BuilderID, policy.BuilderDeny) {
			res.Decision = DecisionDeny
			res.Reason = ReasonBuilderDeny
			return res
		}
	}

	requireActive := len(policy.BuilderRequire) > 0
	if requireActive {
		anyMatch := false
		for _, e := range predOK {
			if buildergate.Required(e.BuilderID, policy.BuilderRequire) {
				anyMatch = true
				break
			}
		}
		if !anyMatch {
			res.Decision = DecisionDeny
			res.Reason = ReasonBuilderRequireMiss
			return res
		}
	}

	var candidates []ciptypes.Envelope
	for _, e := range predOK {
		if buildergate.Denied(e.BuilderID, policy.BuilderDeny) {
			continue
		}
		if requireActive && !buildergate.Required(e.BuilderID, policy.BuilderRequire) {
			continue
		}
		candidates = append(candidates, e)
	}

	seen := make(map[string]bool, len(candidates))
	ids := make([]string, 0, len(candidates))
	for _, e := range candidates {
		if seen[e.EnvelopeID] {
			continue
		}
		seen[e.EnvelopeID] = true
		ids = append(ids, e.EnvelopeID)
	}

	if len(ids) < quorumK {
		res.Decision = DecisionDeny
		res.Reason = ReasonQuorumFail
		return res
	}

	sort.Strings(ids)

	res.Decision = DecisionAllow
	res.Reason = ReasonAdmitVerified
	res.EnvelopeIDs = ids
	return res
}

func isTrusted(e ciptypes.Envelope, roots []ciptypes.TrustRoot) bool {
	for _, r := range roots {
		if rootbind.Binds(r, e) {
			return true
		}
	}
	return false
}

// Package sealhex computes the audit_digest that seals the admission
// ledger (see docs/ledger-seal-format.md).
package sealhex

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"

	"github.com/terminus/slsacip/cipkernel/ciptypes"
)

// auditResult mirrors the reduced per-pull shape required in the audit
// payload: {request_id, decision, reason, envelope_ids}. Field order below
// is alphabetical by JSON key so json.Marshal emits sorted-key, compact
// canonical JSON.
type auditResult struct {
	Decision    string   `json:"decision"`
	EnvelopeIDs []string `json:"envelope_ids"`
	Reason      string   `json:"reason"`
	RequestID   string   `json:"request_id"`
}

// auditPayload mirrors the fields docs/ledger-seal-format.md requires in
// the audit_digest payload. Field order below is alphabetical by JSON key
// so json.Marshal emits sorted-key, compact canonical JSON.
type auditPayload struct {
	BuilderFingerprint   string        `json:"builder_fingerprint"`
	DenyFingerprint      string        `json:"deny_fingerprint"`
	PolicyPacks          []string      `json:"policy_packs"`
	PredicateFingerprint string        `json:"predicate_fingerprint"`
	QuorumK              int           `json:"quorum_k"`
	Results              []auditResult `json:"results"`
	RevokeFingerprint    string        `json:"revoke_fingerprint"`
	Seed                 string        `json:"seed"`
	TrustFingerprint     string        `json:"trust_fingerprint"`
}

// AuditHex computes the lowercase hex SHA-256 of the canonical JSON audit
// payload derived from report.
func AuditHex(report ciptypes.Report) string {
	results := make([]auditResult, 0, len(report.Results))
	for _, r := range report.Results {
		ids := r.EnvelopeIDs
		if ids == nil {
			ids = []string{}
		}
		results = append(results, auditResult{
			Decision:    r.Decision,
			EnvelopeIDs: ids,
			Reason:      r.Reason,
			RequestID:   r.RequestID,
		})
	}

	payload := auditPayload{
		BuilderFingerprint:   report.BuilderFingerprint,
		DenyFingerprint:      report.DenyFingerprint,
		PolicyPacks:          report.PolicyPacks,
		PredicateFingerprint: report.PredicateFingerprint,
		QuorumK:              report.QuorumK,
		Results:              results,
		RevokeFingerprint:    report.RevokeFingerprint,
		Seed:                 report.Seed,
		TrustFingerprint:     report.TrustFingerprint,
	}

	b, err := json.Marshal(payload)
	if err != nil {
		return ""
	}
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:])
}

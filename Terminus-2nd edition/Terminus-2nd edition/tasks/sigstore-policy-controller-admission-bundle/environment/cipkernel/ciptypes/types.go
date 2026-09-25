// Package ciptypes holds the shared data types passed between slsacip's
// loading, gating, and sealing stages.
package ciptypes

import "time"

// TrustRoot is a Fulcio-style trust anchor loaded from trust_roots_dir.
type TrustRoot struct {
	RootID      string `json:"root_id"`
	IssuerGlob  string `json:"issuer_glob"`
	SubjectGlob string `json:"subject_glob"`
}

// Envelope is a Cosign-style offline attestation envelope loaded from
// envelopes_dir.
type Envelope struct {
	EnvelopeID    string `json:"envelope_id"`
	Issuer        string `json:"issuer"`
	Subject       string `json:"subject"`
	PredicateType string `json:"predicate_type"`
	BuilderID     string `json:"builder_id"`
	SubjectDigest string `json:"subject_digest"`
}

// Revocation seals a subject digest as revoked for a half-open time window.
type Revocation struct {
	SubjectDigest string    `json:"subject_digest"`
	Start         time.Time `json:"start"`
	End           time.Time `json:"end"`
}

// PolicyPack is a single named policy pack loaded from policies_root.
type PolicyPack struct {
	Name           string
	BuilderDeny    []string
	BuilderRequire []string
	DigestDenyPins []string
	PredicateAllow []string
	Revocations    []Revocation
}

// MergedPolicy is the result of selecting, shuffling, and merging the
// configured policy packs.
type MergedPolicy struct {
	DigestDenyPins []string
	PredicateAllow []string
	BuilderDeny    []string
	BuilderRequire []string
	Revocations    []Revocation
}

// Pull is a single image pull admission request.
type Pull struct {
	RequestID string    `json:"request_id"`
	Image     string    `json:"image"`
	Timestamp time.Time `json:"timestamp"`
}

// PullResult is the per-pull admission decision recorded in the ledger.
type PullResult struct {
	RequestID   string   `json:"request_id"`
	Image       string   `json:"image"`
	Decision    string   `json:"decision"`
	Reason      string   `json:"reason"`
	EnvelopeIDs []string `json:"envelope_ids"`
}

// WitnessSnapshot is staged at /app/state/slsacip/trust-witness.json
// after policy merge and before the ledger is sealed.
type WitnessSnapshot struct {
	Seed                 string   `json:"seed"`
	QuorumK              int      `json:"quorum_k"`
	PolicyPacks          []string `json:"policy_packs"`
	TrustFingerprint     string   `json:"trust_fingerprint"`
	DenyFingerprint      string   `json:"deny_fingerprint"`
	RevokeFingerprint    string   `json:"revoke_fingerprint"`
	PredicateFingerprint string   `json:"predicate_fingerprint"`
	BuilderFingerprint   string   `json:"builder_fingerprint"`
}

// Report is the sealed admission ledger written to --output.
type Report struct {
	Schema               string       `json:"schema"`
	Seed                 string       `json:"seed"`
	QuorumK              int          `json:"quorum_k"`
	PolicyPacks          []string     `json:"policy_packs"`
	TrustFingerprint     string       `json:"trust_fingerprint"`
	DenyFingerprint      string       `json:"deny_fingerprint"`
	RevokeFingerprint    string       `json:"revoke_fingerprint"`
	PredicateFingerprint string       `json:"predicate_fingerprint"`
	BuilderFingerprint   string       `json:"builder_fingerprint"`
	Results              []PullResult `json:"results"`
	AuditDigest          string       `json:"audit_digest"`
}

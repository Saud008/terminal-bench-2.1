package schema

// DenyReasons is the fixed set of deny codes from
// /app/docs/jkt-thumbprint-policy.md. Every session's DenyTotals map must
// carry all of these keys, defaulting to zero, from the moment it is
// created.
var DenyReasons = []string{
	"ticket_invalid",
	"alg_rejected",
	"bad_signature",
	"jkt_mismatch",
	"htm_mismatch",
	"htu_mismatch",
	"iat_skew",
	"jti_replay",
}

// NewDenyTotals returns a fresh map pre-populated with every deny reason at
// zero.
func NewDenyTotals() map[string]int {
	out := make(map[string]int, len(DenyReasons))
	for _, r := range DenyReasons {
		out[r] = 0
	}
	return out
}

// OpenRequest is the POST /gate/session/open payload. The dpop_proof must be
// a fresh DPoP-style compact JWS whose embedded jwk becomes the pinned key
// for the session (see /app/docs/vault-hmac-bind.md).
type OpenRequest struct {
	Principal string `json:"principal"`
	Session   string `json:"session"`
	DPoPProof string `json:"dpop_proof"`
}

// CheckRequest is the POST /gate/proof/check payload.
type CheckRequest struct {
	Principal  string `json:"principal"`
	Session    string `json:"session"`
	BindTicket string `json:"bind_ticket"`
	DPoPProof  string `json:"dpop_proof"`
}

// CommitRequest is the POST /gate/audit/commit payload.
type CommitRequest struct {
	Principal string `json:"principal"`
	Session   string `json:"session"`
}

// JWK is the minimal EC public key carried in a proof header.
type JWK struct {
	Kty string `json:"kty"`
	Crv string `json:"crv"`
	X   string `json:"x"`
	Y   string `json:"y"`
}

// ProofHeader is the decoded first segment of a compact DPoP proof.
type ProofHeader struct {
	Typ string `json:"typ"`
	Alg string `json:"alg"`
	JWK JWK    `json:"jwk"`
}

// ProofPayload is the decoded second segment of a compact DPoP proof.
type ProofPayload struct {
	Jti string `json:"jti"`
	Htm string `json:"htm"`
	Htu string `json:"htu"`
	Iat int64  `json:"iat"`
}

// ChainEvent records a single admit/deny decision for chainhead staging.
type ChainEvent struct {
	Seq     int    `json:"seq"`
	Jti     string `json:"jti"`
	Verdict string `json:"verdict"`
	Reason  string `json:"reason,omitempty"`
}

// SessionState is the in-memory record for one (principal, session) pair,
// created at open time and updated on every proof-check decision.
type SessionState struct {
	Principal     string
	Session       string
	JKT           string
	BindTicket    string
	AdmittedTotal int
	DeniedTotal   int
	DenyTotals    map[string]int
	ChainSeq      int
	ChainHead     string
	ChainEvents   []ChainEvent
}

// Clone returns a deep-enough copy safe for storing back after mutation.
func (s SessionState) Clone() SessionState {
	out := s
	out.DenyTotals = make(map[string]int, len(s.DenyTotals))
	for k, v := range s.DenyTotals {
		out.DenyTotals[k] = v
	}
	out.ChainEvents = make([]ChainEvent, len(s.ChainEvents))
	copy(out.ChainEvents, s.ChainEvents)
	return out
}

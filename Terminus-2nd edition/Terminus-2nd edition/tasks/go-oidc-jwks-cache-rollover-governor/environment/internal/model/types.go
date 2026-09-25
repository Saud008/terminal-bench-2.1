package model

type JWKSKey struct {
    KID    string `json:"kid"`
    Alg    string `json:"alg"`
    Status string `json:"status"`
}

type TimelineEvent struct {
    Epoch          int       `json:"epoch"`
    EventType      string    `json:"event_type"`
    Keys           []JWKSKey `json:"keys"`
    CacheMaxAgeSec int       `json:"cache_max_age_sec"`
    GraceWindowSec int       `json:"grace_window_sec"`
}

type TokenRecord struct {
    TokenID         string   `json:"token_id"`
    KID             string   `json:"kid"`
    Iss             string   `json:"iss"`
    Aud             []string `json:"aud"`
    IAT             int64    `json:"iat"`
    EXP             int64    `json:"exp"`
    SignatureEpoch  int      `json:"signature_epoch"`
}

type Policy struct {
    Issuer     string   `json:"issuer"`
    Audiences  []string `json:"audiences"`
}

type TranscriptStage struct {
    Engine           string          `json:"engine"`
    Scenario         string          `json:"scenario"`
    Timeline         []TimelineEvent `json:"timeline"`
    Tokens           []TokenRecord   `json:"tokens"`
    Policy           Policy          `json:"policy"`
    TranscriptDigest string          `json:"transcript_digest"`
}

type CacheSnapshot struct {
    Scenario         string    `json:"scenario"`
    ActiveKeys       []JWKSKey `json:"active_keys"`
    RetiredKeys      []JWKSKey `json:"retired_keys"`
    RevokedKids      []string  `json:"revoked_kids"`
    CacheMaxAgeSec   int       `json:"cache_max_age_sec"`
    GraceWindowSec   int       `json:"grace_window_sec"`
    LastTimelineEpoch int      `json:"last_timeline_epoch"`
}

type HydrateRevision struct {
    HydrateRevision int `json:"hydrate_revision"`
}

type VerificationDecision struct {
    TokenID    string `json:"token_id"`
    Verdict    string `json:"verdict"`
    ReasonCode string `json:"reason_code"`
}

type DecisionsFile struct {
    Scenario  string                 `json:"scenario"`
    Decisions []VerificationDecision `json:"decisions"`
}

type GovernanceReport struct {
    Scenario      string                 `json:"scenario"`
    DecisionCount int                    `json:"decision_count"`
    Decisions     []VerificationDecision `json:"decisions"`
    ReportDigest  string                 `json:"report_digest"`
}

package model

type JWKSKey struct {
    KID string `json:"kid"`
    Use string `json:"use"`
    Alg string `json:"alg,omitempty"`
}

type JWKS struct {
    Keys []JWKSKey `json:"keys"`
}

type X509SVID struct {
    Serial        string `json:"serial"`
    SPIFFEID      string `json:"spiffe_id"`
    RotationEpoch int    `json:"rotation_epoch,omitempty"`
    LastSeenEpoch int    `json:"last_seen_epoch"`
}

type TrustDomainBundle struct {
    BundleEpoch          int        `json:"bundle_epoch"`
    TrustDomain          string     `json:"trust_domain"`
    JWKS                 JWKS       `json:"jwks"`
    X509SVID             []X509SVID `json:"x509_svid"`
    FederationAllowlist  []string   `json:"federation_allowlist"`
}

type PairCapture struct {
    Engine        string            `json:"engine"`
    Scenario      string            `json:"scenario"`
    Left          TrustDomainBundle `json:"left"`
    Right         TrustDomainBundle `json:"right"`
    CaptureDigest string            `json:"capture_digest"`
}

type RevisionFile struct {
    SealCounter int `json:"seal_counter"`
}

type DiffChange struct {
    Path       string `json:"path"`
    ChangeType string `json:"change_type"`
    LeftValue  string `json:"left_value,omitempty"`
    RightValue string `json:"right_value,omitempty"`
}

type DiffReport struct {
    Scenario     string       `json:"scenario"`
    ChangeCount  int          `json:"change_count"`
    Changes      []DiffChange `json:"changes"`
    ReportDigest string       `json:"report_digest"`
}

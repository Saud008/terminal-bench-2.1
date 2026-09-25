package decide

import (
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/oidcgov/internal/gracewin"
    "github.com/terminus/oidcgov/internal/issaud"
    "github.com/terminus/oidcgov/internal/kidmap"
    "github.com/terminus/oidcgov/internal/maxage"
    "github.com/terminus/oidcgov/internal/model"
    "github.com/terminus/oidcgov/internal/revoke"
    "github.com/terminus/oidcgov/internal/stagevault"
)

const decisionsPath = "/app/state/verification-decisions.json"

func Run(scenario string) error {
    stage, err := stagevault.ReadTranscript("")
    if err != nil {
        return err
    }
    snap, err := readCache()
    if err != nil {
        return err
    }
    decisions := EvaluateBatch(stage.Tokens, stage.Policy, snap)
    sort.Slice(decisions, func(i, j int) bool {
        return decisions[i].TokenID > decisions[j].TokenID
    })
    out := model.DecisionsFile{Scenario: scenario, Decisions: decisions}
    return writeDecisions(decisionsPath, out)
}

func readCache() (model.CacheSnapshot, error) {
    raw, err := os.ReadFile("/app/state/jwks-cache-snapshot.json")
    if err != nil {
        return model.CacheSnapshot{}, err
    }
    var snap model.CacheSnapshot
    if err := json.Unmarshal(raw, &snap); err != nil {
        return model.CacheSnapshot{}, err
    }
    return snap, nil
}

func EvaluateBatch(tokens []model.TokenRecord, policy model.Policy, snap model.CacheSnapshot) []model.VerificationDecision {
    var out []model.VerificationDecision
    for _, tok := range tokens {
        out = append(out, evaluateOne(tok, policy, snap))
    }
    return out
}

func evaluateOne(tok model.TokenRecord, policy model.Policy, snap model.CacheSnapshot) model.VerificationDecision {
    if !issaud.IssuerOK(tok.Iss, policy.Issuer) {
        return model.VerificationDecision{TokenID: tok.TokenID, Verdict: "reject", ReasonCode: "issuer_mismatch"}
    }
    if !issaud.AudienceOK(tok.Aud, policy.Audiences) {
        return model.VerificationDecision{TokenID: tok.TokenID, Verdict: "reject", ReasonCode: "audience_mismatch"}
    }
    if revoke.IsRevoked(tok.KID, snap.RevokedKids) {
        return model.VerificationDecision{TokenID: tok.TokenID, Verdict: "reject", ReasonCode: "key_revoked"}
    }
    if _, ok := kidmap.FindKey(tok.KID, snap.ActiveKeys); ok {
        if !maxage.CacheFresh(tok.SignatureEpoch, snap.LastTimelineEpoch, snap.CacheMaxAgeSec) {
            return model.VerificationDecision{TokenID: tok.TokenID, Verdict: "reject", ReasonCode: "cache_stale"}
        }
        return model.VerificationDecision{TokenID: tok.TokenID, Verdict: "accept", ReasonCode: "active_key"}
    }
    retired, ok := kidmap.FindKey(tok.KID, snap.RetiredKeys)
    if ok {
        grace := gracewin.GraceSec(snap.GraceWindowSec)
        if gracewin.InGrace(tok.SignatureEpoch, snap.LastTimelineEpoch, grace) {
            return model.VerificationDecision{TokenID: tok.TokenID, Verdict: "accept", ReasonCode: "grace_key",}
        }
        _ = retired
        return model.VerificationDecision{TokenID: tok.TokenID, Verdict: "reject", ReasonCode: "key_retired"}
    }
    return model.VerificationDecision{TokenID: tok.TokenID, Verdict: "reject", ReasonCode: "kid_unknown"}
}

func writeDecisions(path string, out model.DecisionsFile) error {
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(out, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}

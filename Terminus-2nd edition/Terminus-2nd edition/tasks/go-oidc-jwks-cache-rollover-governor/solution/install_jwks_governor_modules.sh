#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
find /app/internal /app/cmd -name "*.go" -exec sed -i "s/\r$//" {} +

cat > /app/internal/decide/batch.go <<'GOEOF_internal_decide_batch_go'
package decide

import (
    "encoding/json"
    "os"
    "path/filepath"
    "sort"
    "strings"

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
    snap, retiredEpochs, err := readCacheWithRetired(stage.Timeline)
    if err != nil {
        return err
    }
    decisions := EvaluateBatch(stage.Tokens, stage.Policy, snap, retiredEpochs)
    sort.Slice(decisions, func(i, j int) bool {
        return decisions[i].TokenID < decisions[j].TokenID
    })
    out := model.DecisionsFile{Scenario: scenario, Decisions: decisions}
    return writeDecisions(decisionsPath, out)
}

func readCacheWithRetired(timeline []model.TimelineEvent) (model.CacheSnapshot, map[string]int, error) {
    raw, err := os.ReadFile("/app/state/jwks-cache-snapshot.json")
    if err != nil {
        return model.CacheSnapshot{}, nil, err
    }
    var snap model.CacheSnapshot
    if err := json.Unmarshal(raw, &snap); err != nil {
        return model.CacheSnapshot{}, nil, err
    }
    retired := map[string]int{}
    for _, ev := range timeline {
        for _, k := range ev.Keys {
            if k.Status == "retired" {
                retired[strings.ToLower(strings.TrimSpace(k.KID))] = ev.Epoch
            }
        }
    }
    return snap, retired, nil
}

func EvaluateBatch(tokens []model.TokenRecord, policy model.Policy, snap model.CacheSnapshot, retiredEpochs map[string]int) []model.VerificationDecision {
    var out []model.VerificationDecision
    for _, tok := range tokens {
        out = append(out, evaluateOne(tok, policy, snap, retiredEpochs))
    }
    return out
}

func evaluateOne(tok model.TokenRecord, policy model.Policy, snap model.CacheSnapshot, retiredEpochs map[string]int) model.VerificationDecision {
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
    if _, ok := kidmap.FindKey(tok.KID, snap.RetiredKeys); ok {
        retiredEpoch := retiredEpochs[strings.ToLower(strings.TrimSpace(tok.KID))]
        grace := gracewin.GraceSec(snap.GraceWindowSec)
        if gracewin.InGrace(tok.SignatureEpoch, retiredEpoch, grace) {
            return model.VerificationDecision{TokenID: tok.TokenID, Verdict: "accept", ReasonCode: "grace_key"}
        }
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
GOEOF_internal_decide_batch_go

cat > /app/internal/gracewin/window.go <<'GOEOF_internal_gracewin_window_go'
package gracewin

import (
    "os"
    "strconv"
)

const DefaultGrace = 120

func GraceSec(fallback int) int {
    if raw := os.Getenv("TB3_GRACE_SEC"); raw != "" {
        if v, err := strconv.Atoi(raw); err == nil && v >= 0 {
            return v
        }
    }
    if fallback > 0 {
        return fallback
    }
    return DefaultGrace
}

func InGrace(signatureEpoch, retiredEpoch, graceSec int) bool {
    return signatureEpoch >= retiredEpoch && signatureEpoch <= retiredEpoch+graceSec
}
GOEOF_internal_gracewin_window_go

cat > /app/internal/hydrate/pass.go <<'GOEOF_internal_hydrate_pass_go'
package hydrate

import (
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/oidcgov/internal/model"
    "github.com/terminus/oidcgov/internal/stagevault"
)

const (
    cachePath    = "/app/state/jwks-cache-snapshot.json"
    revisionPath = "/app/state/hydrate-revision.json"
)

func Run(scenario string) error {
    stage, err := stagevault.ReadTranscript("")
    if err != nil {
        return err
    }
    snap := BuildSnapshot(stage.Timeline, scenario)
    if err := writeSnapshot(cachePath, snap); err != nil {
        return err
    }
    return bumpRevision()
}

func BuildSnapshot(timeline []model.TimelineEvent, scenario string) model.CacheSnapshot {
    snap := model.CacheSnapshot{Scenario: scenario}
    for _, ev := range timeline {
        snap.LastTimelineEpoch = ev.Epoch
        snap.CacheMaxAgeSec = ev.CacheMaxAgeSec
        snap.GraceWindowSec = ev.GraceWindowSec
        snap.ActiveKeys = nil
        snap.RetiredKeys = nil
        snap.RevokedKids = nil
        for _, k := range ev.Keys {
            switch k.Status {
            case "active":
                snap.ActiveKeys = append(snap.ActiveKeys, k)
            case "retired":
                snap.RetiredKeys = append(snap.RetiredKeys, k)
            case "revoked":
                snap.RevokedKids = append(snap.RevokedKids, k.KID)
            }
        }
    }
    return snap
}

func writeSnapshot(path string, snap model.CacheSnapshot) error {
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(snap, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}

func bumpRevision() error {
    var rev model.HydrateRevision
    if raw, err := os.ReadFile(revisionPath); err == nil {
        _ = json.Unmarshal(raw, &rev)
    }
    rev.HydrateRevision = rev.HydrateRevision + 1
    data, err := json.MarshalIndent(rev, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(revisionPath, data, 0o644)
}
GOEOF_internal_hydrate_pass_go

cat > /app/internal/issaud/bind.go <<'GOEOF_internal_issaud_bind_go'
package issaud

import "strings"

func AudienceOK(tokenAud, policyAud []string) bool {
    if len(policyAud) == 0 {
        return true
    }
    policySet := map[string]struct{}{}
    for _, pa := range policyAud {
        policySet[strings.TrimSpace(pa)] = struct{}{}
    }
    for _, ta := range tokenAud {
        if _, ok := policySet[strings.TrimSpace(ta)]; !ok {
            return false
        }
    }
    return true
}

func IssuerOK(tokenIss, policyIss string) bool {
    return strings.TrimSpace(strings.ToLower(tokenIss)) == strings.TrimSpace(strings.ToLower(policyIss))
}
GOEOF_internal_issaud_bind_go

cat > /app/internal/kidmap/lookup.go <<'GOEOF_internal_kidmap_lookup_go'
package kidmap

import (
    "strings"

    "github.com/terminus/oidcgov/internal/model"
)

func FindKey(kid string, keys []model.JWKSKey) (model.JWKSKey, bool) {
    want := strings.TrimSpace(strings.ToLower(kid))
    for _, k := range keys {
        if strings.TrimSpace(strings.ToLower(k.KID)) == want {
            return k, true
        }
    }
    return model.JWKSKey{}, false
}
GOEOF_internal_kidmap_lookup_go

cat > /app/internal/maxage/ttl.go <<'GOEOF_internal_maxage_ttl_go'
package maxage

func CacheFresh(signatureEpoch, lastTimelineEpoch, maxAgeSec int) bool {
    age := lastTimelineEpoch - signatureEpoch
    return age <= maxAgeSec
}
GOEOF_internal_maxage_ttl_go

cat > /app/internal/revoke/filter.go <<'GOEOF_internal_revoke_filter_go'
package revoke

import "strings"

func IsRevoked(kid string, revoked []string) bool {
    want := strings.TrimSpace(strings.ToLower(kid))
    for _, r := range revoked {
        if strings.TrimSpace(strings.ToLower(r)) == want {
            return true
        }
    }
    return false
}
GOEOF_internal_revoke_filter_go

sed -i 's/return timeline\[i\]\.Epoch > timeline\[j\]\.Epoch/return timeline[i].Epoch < timeline[j].Epoch/' /app/internal/timeline/load.go
sed -i 's/return decisions\[i\]\.TokenID > decisions\[j\]\.TokenID/return decisions[i].TokenID < decisions[j].TokenID/' /app/internal/publish/report_publish.go
sed -i 's/computeDigest(stage.Scenario, stage.Timeline, stage.Tokens)/computeDigest(stage.Scenario, stage.Timeline, stage.Tokens, stage.Policy)/' /app/internal/stagevault/transcript.go
sed -i 's/func computeDigest(scenario string, timeline \[\]model.TimelineEvent, tokens \[\]model.TokenRecord) (string, error) {/func computeDigest(scenario string, timeline []model.TimelineEvent, tokens []model.TokenRecord, policy model.Policy) (string, error) {/' /app/internal/stagevault/transcript.go
sed -i 's/"scenario": scenario,/"policy": policy,\n        "scenario": scenario,/' /app/internal/stagevault/transcript.go

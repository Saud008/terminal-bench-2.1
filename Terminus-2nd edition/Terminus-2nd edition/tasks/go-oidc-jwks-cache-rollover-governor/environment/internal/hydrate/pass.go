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
    if len(timeline) == 0 {
        return snap
    }
    ev := timeline[len(timeline)-1]
    snap.LastTimelineEpoch = ev.Epoch
    snap.CacheMaxAgeSec = ev.CacheMaxAgeSec
    snap.GraceWindowSec = ev.GraceWindowSec
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
    rev.HydrateRevision = rev.HydrateRevision
    data, err := json.MarshalIndent(rev, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(revisionPath, data, 0o644)
}

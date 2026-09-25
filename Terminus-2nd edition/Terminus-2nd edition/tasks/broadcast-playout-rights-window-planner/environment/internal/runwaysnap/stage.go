package runwaysnap

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"

    "github.com/terminus/gridplan/internal/model"
)

func WriteRunwaySnap(scenario string) error {
    bundle, err := readBundle()
    if err != nil {
        return err
    }
    nodes := make([]map[string]any, 0, len(bundle.Programs))
    edges := make([]map[string]any, 0, len(bundle.Programs))
    for _, prog := range bundle.Programs {
        nodes = append(nodes, map[string]any{
            "kind": "program", "id": prog.ProgramID, "feed_id": prog.FeedID,
        })
        edges = append(edges, map[string]any{
            "kind": "program_feed", "program_id": prog.ProgramID, "feed_id": prog.FeedID,
        })
    }
    fp := runwayDigest(bundle)
    body := map[string]any{
        "scenario": scenario,
        "engine":   "gridplan",
        "runway_digest": fp,
        "nodes": nodes,
        "edges": edges,
    }
    raw, err := json.MarshalIndent(body, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile("/app/state/runway-snapshot.json", append(raw, '\n'), 0o644)
}

func readBundle() (*model.ScheduleBundle, error) {
    raw, err := os.ReadFile("/app/state/active-grid.json")
    if err != nil {
        return nil, err
    }
    var bundle model.ScheduleBundle
    if err := json.Unmarshal(raw, &bundle); err != nil {
        return nil, err
    }
    return &bundle, nil
}

func runwayDigest(bundle *model.ScheduleBundle) string {
    h := sha256.New()
    h.Write([]byte(bundle.Seed))
    for _, p := range bundle.Programs {
        h.Write([]byte(p.ProgramID))
    }
    return hex.EncodeToString(h.Sum(nil))
}

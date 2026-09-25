package constraintgraph

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"

    "github.com/terminus/ttalloc/internal/model"
)

func WriteGraph(scenario string) error {
    bundle, err := readBundle()
    if err != nil {
        return err
    }
    nodes := make([]map[string]any, 0, len(bundle.Sections)*2)
    edges := make([]map[string]any, 0, len(bundle.Sections)*2)
    for _, sec := range bundle.Sections {
        nodes = append(nodes, map[string]any{
            "kind": "section", "id": sec.SectionID, "requires_lab": sec.RequiresLab,
        })
        edges = append(edges, map[string]any{
            "kind": "section_teacher", "section_id": sec.SectionID, "teacher_id": sec.TeacherID,
        })
        if sec.RequiresLab {
            edges = append(edges, map[string]any{
                "kind": "lab_requirement", "section_id": sec.SectionID,
            })
        }
    }
    fp := fingerprint(bundle)
    body := map[string]any{
        "scenario": scenario,
        "engine":   "ttalloc",
        "graph_fingerprint": fp,
        "nodes": nodes,
        "edges": edges,
    }
    raw, err := json.MarshalIndent(body, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile("/app/state/constraint-graph.json", append(raw, '\n'), 0o644)
}

func readBundle() (*model.RosterBundle, error) {
    raw, err := os.ReadFile("/app/state/active-roster.json")
    if err != nil {
        return nil, err
    }
    var bundle model.RosterBundle
    if err := json.Unmarshal(raw, &bundle); err != nil {
        return nil, err
    }
    return &bundle, nil
}

func fingerprint(bundle *model.RosterBundle) string {
    h := sha256.New()
    h.Write([]byte(bundle.Seed))
    for _, s := range bundle.Sections {
        h.Write([]byte(s.SectionID))
    }
    return hex.EncodeToString(h.Sum(nil))
}

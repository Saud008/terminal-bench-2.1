package index

import (
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/filingatlas/internal/model"
    "github.com/terminus/filingatlas/internal/nxtg01"
    "github.com/terminus/filingatlas/internal/nxtg06"
)

const (
    graphPath    = "/app/state/party-graph.json"
    revisionPath = "/app/state/index-revision.json"
)

func Run(scenario string) error {
    stage, err := stagevault.ReadBundle("")
    if err != nil {
        return err
    }
    graph := partygraph.BuildGraph(scenario, stage.Parties)
    if err := writeGraph(graphPath, graph); err != nil {
        return err
    }
    return bumpRevision()
}

func writeGraph(path string, graph model.PartyGraph) error {
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(graph, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}

func bumpRevision() error {
    var rev model.IndexRevision
    if raw, err := os.ReadFile(revisionPath); err == nil {
        _ = json.Unmarshal(raw, &rev)
    }
    rev.IndexRevision = rev.IndexRevision + 1
    data, err := json.MarshalIndent(rev, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(revisionPath, data, 0o644)
}

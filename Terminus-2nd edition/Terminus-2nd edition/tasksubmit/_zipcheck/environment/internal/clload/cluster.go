package clload

import (
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/snapretctl/internal/model"
)

func LoadCluster(scenario, fixtureRoot string) (model.ClusterJSON, error) {
    if fixtureRoot == "" {
        fixtureRoot = "/app/fixtures"
    }
    clusterPath := filepath.Join(fixtureRoot, "clusters", scenario, "cluster.json")
    raw, err := os.ReadFile(clusterPath)
    if err != nil {
        return model.ClusterJSON{}, err
    }
    var cluster model.ClusterJSON
    if err := json.Unmarshal(raw, &cluster); err != nil {
        return model.ClusterJSON{}, err
    }
    return cluster, nil
}

package csibridge

import (
    "github.com/terminus/snapretctl/internal/clload"
    "github.com/terminus/snapretctl/internal/model"
    "github.com/terminus/snapretctl/internal/fltstore"
)

func MaterializeFleetGraph(scenario, fixtureRoot string) (model.FleetGraphFile, error) {
    cluster, err := clload.LoadCluster(scenario, fixtureRoot)
    if err != nil {
        return model.FleetGraphFile{}, err
    }
    return model.FleetGraphFile{
        Engine: "snapretctl", Scenario: scenario, Cluster: cluster,
    }, nil
}

func PersistFleetGraph(snap model.FleetGraphFile) error {
    return fltstore.WriteFleetGraph("", snap)
}

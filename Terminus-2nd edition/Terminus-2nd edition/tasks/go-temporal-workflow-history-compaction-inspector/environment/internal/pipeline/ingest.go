package pipeline

import (
    "github.com/terminus/wfhistctl/internal/fixtureio"
    "github.com/terminus/wfhistctl/internal/eventcache"
    "github.com/terminus/wfhistctl/internal/model"
)

func MaterializeHistory(ns, scenario, fixtureDir string) (model.HistoryStaging, error) {
    events, err := fixtureio.LoadHistory(ns, scenario, fixtureDir)
    if err != nil {
        return model.HistoryStaging{}, err
    }
    return model.HistoryStaging{
        Engine:     "wfhistctl",
        Namespace:  ns,
        Scenario:   scenario,
        EventCount: len(events),
        Events:     events,
    }, nil
}

func PersistStaging(snap model.HistoryStaging) error {
    return eventcache.WriteStage("", snap)
}

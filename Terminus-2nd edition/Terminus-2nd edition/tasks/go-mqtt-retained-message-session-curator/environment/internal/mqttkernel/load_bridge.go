package mqttkernel

import (
    "github.com/edgeiot/mqttsessctl/internal/journalstore"
    "github.com/edgeiot/mqttsessctl/internal/eventloader"
    "github.com/edgeiot/mqttsessctl/internal/model"
)

func LoadBrokerJournal(broker, scenario, fixtureRoot string) (model.SessionStaging, error) {
    events, err := eventloader.LoadJournal(broker, scenario, fixtureRoot)
    if err != nil {
        return model.SessionStaging{}, err
    }
    return model.SessionStaging{
        Engine:     "mqttsessctl",
        Broker:     broker,
        Scenario:   scenario,
        EventCount: len(events),
        Events:     events,
    }, nil
}

func WriteJournalStaging(snap model.SessionStaging) error {
    return journalstore.PersistJournalStage("", snap)
}

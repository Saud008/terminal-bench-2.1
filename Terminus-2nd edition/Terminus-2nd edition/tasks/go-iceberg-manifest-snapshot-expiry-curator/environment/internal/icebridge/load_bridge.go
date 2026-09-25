package icebridge

import (
    "github.com/terminus/iceexpctl/internal/catalogload"
    "github.com/terminus/iceexpctl/internal/model"
    "github.com/terminus/iceexpctl/internal/cursorsnap"
)

func MaterializeTable(scenario, fixtureRoot string) (model.CursorSnapshot, error) {
    table, manifests, err := catalogload.LoadTable(scenario, fixtureRoot)
    if err != nil {
        return model.CursorSnapshot{}, err
    }
    return model.CursorSnapshot{
        Engine:    "iceexpctl",
        Scenario:  scenario,
        Table:     table,
        Manifests: manifests,
    }, nil
}

func PersistCursor(snap model.CursorSnapshot) error {
    return cursorsnap.WriteStage("", snap)
}

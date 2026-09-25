package snapshot

import (
    "encoding/json"
    "os"

    "github.com/terminus/venuetixctl/internal/venuesql"
    "github.com/terminus/venuetixctl/internal/holddigest"
)

const snapshotPath = "/app/state/seat-hold-snapshot.json"

func WriteHoldSnapshot(scenario string) error {
    db, err := dbread.Open("/app/state/event-venue.sqlite")
    if err != nil {
        return err
    }
    defer db.Close()
    meta, err := dbread.ReadMeta(db)
    if err != nil {
        return err
    }
    sections, err := dbread.ReadSections(db)
    if err != nil {
        return err
    }
    holds, err := dbread.ReadHolds(db)
    if err != nil {
        return err
    }
    digest := stagewire.HoldSnapshotDigest(meta, sections, holds)
    body, err := json.Marshal(map[string]any{
        "scenario":         scenario,
        "engine":           "venuetixctl",
        "hold_snapshot_digest":   digest,
        "hold_count":       len(holds),
        "section_count":    len(sections),
    })
    if err != nil {
        return err
    }
    return os.WriteFile(snapshotPath, body, 0o644)
}

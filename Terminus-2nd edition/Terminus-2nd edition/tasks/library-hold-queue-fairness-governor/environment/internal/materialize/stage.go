package materialize

import (
    "encoding/json"
    "os"

    "github.com/terminus/holdfairctl/internal/dbread"
    "github.com/terminus/holdfairctl/internal/snaprollup"
)

const rollupPath = "/app/state/hold-queue-rollup.json"

func WriteQueueRollup(scenario string) error {
    db, err := dbread.Open("/app/state/active-library.db")
    if err != nil {
        return err
    }
    defer db.Close()
    meta, err := dbread.ReadMeta(db)
    if err != nil {
        return err
    }
    patrons, err := dbread.ReadPatrons(db)
    if err != nil {
        return err
    }
    holds, err := dbread.ReadHolds(db)
    if err != nil {
        return err
    }
    digest := snaprollup.RollupFingerprint(meta, patrons, holds)
    body, err := json.Marshal(map[string]any{
        "scenario":          scenario,
        "engine":            "holdfairctl",
        "rollup_fingerprint":    digest,
        "hold_request_count": len(holds),
        "patron_count":      len(patrons),
    })
    if err != nil {
        return err
    }
    return os.WriteFile(rollupPath, body, 0o644)
}

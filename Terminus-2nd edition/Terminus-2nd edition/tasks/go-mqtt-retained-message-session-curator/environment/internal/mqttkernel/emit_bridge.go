package mqttkernel

import (
    "fmt"

    "github.com/edgeiot/mqttsessctl/internal/journalstore"
    "github.com/edgeiot/mqttsessctl/internal/atlasemit"
    "github.com/edgeiot/mqttsessctl/internal/curatormux"
)

func EmitSessionAtlas(broker, scenario, atlasOut, ledgerOut string) error {
    seal, err := curatormux.ReadSeal()
    if err != nil {
        return err
    }
    if seal.CuratorSeal <= 0 {
        return fmt.Errorf("curator_seal must be > 0")
    }
    snap, err := journalstore.LoadJournalStage("")
    if err != nil {
        return err
    }
    if atlasOut == "" {
        atlasOut = "/app/output/subscription-atlas.jsonl"
    }
    if ledgerOut == "" {
        ledgerOut = "/app/output/delivery-ledger.jsonl"
    }
    result := atlasemit.ComposeAtlasExport(snap.Events)
    if err := atlasemit.WriteAtlas(atlasOut, result.Atlas); err != nil {
        return err
    }
    return atlasemit.WriteLedger(ledgerOut, result.Ledger)
}

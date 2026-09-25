package mqttkernel

import (
    "github.com/edgeiot/mqttsessctl/internal/journalstore"
    "github.com/edgeiot/mqttsessctl/internal/model"
    "github.com/edgeiot/mqttsessctl/internal/curatormux"
)

func RunMergePass(broker, scenario string) error {
    snap, err := journalstore.LoadJournalStage("")
    if err != nil {
        return err
    }
    report := curatormux.Analyze(snap.Events)
    report.Scenario = scenario
    if err := curatormux.WriteReport(report); err != nil {
        return err
    }
    seal := curatormux.IncrementCuratorSeal(model.CuratorSeal{})
    return curatormux.WriteSeal(seal)
}

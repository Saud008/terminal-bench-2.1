package workflowglue

import (
    "encoding/json"
    "os"

    "github.com/terminus/auctctl/internal/lotverdict"
    "github.com/terminus/auctctl/internal/scenarioload"
    "github.com/terminus/auctctl/internal/settlementemit"
)

func LoadCatalog(scenario, fixtureDir string) error {
    sc, err := scenarioload.LoadScenario(scenario, fixtureDir)
    if err != nil {
        return err
    }
    return scenarioload.PersistCatalog(sc)
}

func AdjudicateLots(scenario string) error {
    if err := scenarioload.CatalogLoaded(scenario); err != nil {
        return err
    }
    if err := lotverdict.RunAdjudication(); err != nil {
        return err
    }
    return bumpAdjudicationPass()
}

func PublishInvoices(scenario, outPath string) error {
    if err := scenarioload.CatalogLoaded(scenario); err != nil {
        return err
    }
    return settlementemit.PublishInvoices(scenario, outPath)
}

func bumpAdjudicationPass() error {
    path := "/app/state/adjudication-pass.json"
    var body struct {
        AdjudicationPass int `json:"adjudication_pass"`
        FinalizePass     int `json:"finalize_pass"`
    }
    raw, _ := os.ReadFile(path)
    _ = json.Unmarshal(raw, &body)
    body.AdjudicationPass = body.AdjudicationPass + 1
    out, err := json.Marshal(body)
    if err != nil {
        return err
    }
    return os.WriteFile(path, append(out, '\n'), 0o644)
}

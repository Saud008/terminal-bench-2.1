package workflowglue

import (
	"encoding/json"
	"os"

	"github.com/terminus/subledctl/internal/cycleload"
	"github.com/terminus/subledctl/internal/invoicepub"
	"github.com/terminus/subledctl/internal/entitlementrun"
)

func LoadCycle(scenario, fixtureDir string) error {
	sc, err := cycleload.LoadScenario(scenario, fixtureDir)
	if err != nil {
		return err
	}
	return cycleload.PersistCycle(sc)
}

func RunEntitlementPassCmd(scenario string) error {
	if err := cycleload.CycleLoaded(scenario); err != nil {
		return err
	}
	if err := entitlementrun.RunEntitlementPass(); err != nil {
		return err
	}
	return bumpReconcilePass()
}

func PublishInvoices(scenario, outPath string) error {
	if err := cycleload.CycleLoaded(scenario); err != nil {
		return err
	}
	return invoicepub.PublishInvoices(scenario, outPath)
}

func bumpReconcilePass() error {
	path := "/app/state/reconcile-pass.json"
	var body struct {
		ReconcilePass int `json:"reconcile_pass"`
		PublishPass   int `json:"publish_pass"`
	}
	raw, _ := os.ReadFile(path)
	_ = json.Unmarshal(raw, &body)
	body.ReconcilePass = body.ReconcilePass + 1
	out, err := json.Marshal(body)
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(out, '\n'), 0o644)
}

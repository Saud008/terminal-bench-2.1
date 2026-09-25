package orchestrator

import (
	"encoding/json"
	"os"

	"github.com/terminus/borderdocctl/internal/decision"
	"github.com/terminus/borderdocctl/internal/ledger"
	"github.com/terminus/borderdocctl/internal/manifestio"
)

func LoadBundle(scenario, fixtureDir string) error {
	sc, err := manifestio.LoadScenario(scenario, fixtureDir)
	if err != nil {
		return err
	}
	return manifestio.PersistBundle(sc)
}

func EvaluateWindows(scenario string) error {
	if err := manifestio.BundleLoaded(scenario); err != nil {
		return err
	}
	rows, err := decision.EvaluateAll(scenario)
	if err != nil {
		return err
	}
	if err := bumpEvalPass(); err != nil {
		return err
	}
	return decision.WriteDecisions(scenario, rows, "")
}

func PublishLedger(scenario, outPath string) error {
	if err := manifestio.BundleLoaded(scenario); err != nil {
		return err
	}
	return ledger.PublishRows(scenario, outPath)
}

func bumpEvalPass() error {
	path := "/app/state/eval-pass.json"
	var body struct {
		EvalPass    int `json:"eval_pass"`
		PublishPass int `json:"publish_pass"`
	}
	raw, _ := os.ReadFile(path)
	_ = json.Unmarshal(raw, &body)
	body.EvalPass = body.EvalPass + 1
	out, err := json.Marshal(body)
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(out, '\n'), 0o644)
}

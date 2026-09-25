package orchestrate

import (
	"encoding/json"
	"os"

	"github.com/terminus/bbreleasectl/internal/pairscore"
	"github.com/terminus/bbreleasectl/internal/sealpublish"
	"github.com/terminus/bbreleasectl/internal/panelimport"
)

func LoadScenario(scenario, fixtureDir string) error {
	sc, err := panelimport.LoadScenarioFile(scenario, fixtureDir)
	if err != nil {
		return err
	}
	return panelimport.PersistScenario(sc)
}

func EvaluateCrossmatch(scenario string) error {
	if err := panelimport.ScenarioLoaded(scenario); err != nil {
		return err
	}
	if err := pairscore.RunEvaluation(scenario); err != nil {
		return err
	}
	return bumpEvaluationPass()
}

func PublishLedger(scenario, outPath string) error {
	if err := panelimport.ScenarioLoaded(scenario); err != nil {
		return err
	}
	return sealpublish.PublishLedger(scenario, outPath)
}

func bumpEvaluationPass() error {
	path := "/app/state/screening-pass.json"
	var body struct {
		EvaluationPass int `json:"screening_pass"`
		PublishPass    int `json:"seal_pass"`
	}
	raw, _ := os.ReadFile(path)
	_ = json.Unmarshal(raw, &body)
	body.EvaluationPass = body.EvaluationPass + 1
	out, err := json.Marshal(body)
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(out, '\n'), 0o644)
}

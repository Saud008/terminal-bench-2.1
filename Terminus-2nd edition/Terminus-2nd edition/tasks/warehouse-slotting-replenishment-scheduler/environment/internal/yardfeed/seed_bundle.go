package yardfeed

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/whslot/internal/whmodel"
	"github.com/terminus/whslot/internal/replenledger"
)

func LatchScenario(scenario, fixtureDir string) error {
	path := filepath.Join(fixtureDir, "scenarios", scenario, "bundle.json")
	raw, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var bundle whmodel.Bundle
	if err := json.Unmarshal(raw, &bundle); err != nil {
		return err
	}
	if err := os.WriteFile("/app/state/latched-yard.json", append(raw, '\n'), 0o644); err != nil {
		return err
	}
	db, err := replenledger.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	if _, err := db.Exec(`DELETE FROM velocity_ranks; DELETE FROM wave_tasks`); err != nil {
		return err
	}
	return replenledger.SetMeta(db, "wave_id", bundle.WaveID)
}

func ReadActive() (whmodel.Bundle, error) {
	raw, err := os.ReadFile("/app/state/latched-yard.json")
	if err != nil {
		return whmodel.Bundle{}, err
	}
	var b whmodel.Bundle
	if err := json.Unmarshal(raw, &b); err != nil {
		return whmodel.Bundle{}, err
	}
	if b.WaveID == "" {
		return whmodel.Bundle{}, fmt.Errorf("missing wave_id")
	}
	return b, nil
}

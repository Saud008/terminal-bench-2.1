package replay

import (
	"encoding/json"
	"os"

	"github.com/terminus/gocron-overlap-repair/internal/ledger"
	"github.com/terminus/gocron-overlap-repair/internal/model"
	"github.com/terminus/gocron-overlap-repair/internal/staging"
)

func BuildLedgerExport(store *ledger.Store, stagingPath, seed, scenario string) (model.LedgerExport, error) {
	snap, err := staging.ReadSnapshot(stagingPath)
	if err != nil {
		return model.LedgerExport{}, err
	}
	rows, err := store.List()
	if err != nil {
		return model.LedgerExport{}, err
	}
	if rows == nil {
		rows = []model.ExecutionRow{}
	}
	fires, dedup, err := store.CountFires()
	if err != nil {
		return model.LedgerExport{}, err
	}
	_ = snap
	return model.LedgerExport{
		Seed: seed, Scenario: scenario, Executions: rows,
		FireCount: fires, DedupCount: dedup,
	}, nil
}

func WriteLedgerExport(path string, exp model.LedgerExport) error {
	raw, err := json.MarshalIndent(exp, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}

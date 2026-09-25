package replay

import (
	"encoding/json"
	"fmt"
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
	if snap.Engine != "croncalc" {
		return model.LedgerExport{}, fmt.Errorf("staging engine must be croncalc")
	}
	wantDigest := staging.ComputeFiresDigest(snap.PlannedFires)
	if snap.FiresDigest != wantDigest {
		return model.LedgerExport{}, fmt.Errorf("fires_digest mismatch")
	}
	genState, err := staging.ReadGeneration(staging.GenerationPath())
	if err != nil {
		return model.LedgerExport{}, fmt.Errorf("missing replay generation state")
	}
	if genState.Seed != seed || genState.Scenario != scenario {
		return model.LedgerExport{}, fmt.Errorf("generation seed/scenario mismatch")
	}
	if snap.ReplayGeneration != genState.Generation || genState.Generation < 1 {
		return model.LedgerExport{}, fmt.Errorf("replay generation not advanced")
	}
	rows, err := store.List()
	if err != nil {
		return model.LedgerExport{}, err
	}
	if rows == nil {
		rows = []model.ExecutionRow{}
	}
	planned := map[string]map[int64]struct{}{}
	for _, pf := range snap.PlannedFires {
		if planned[pf.JobID] == nil {
			planned[pf.JobID] = map[int64]struct{}{}
		}
		planned[pf.JobID][pf.AtMs] = struct{}{}
	}
	for _, r := range rows {
		if r.Deduped {
			continue
		}
		if _, ok := planned[r.JobID][r.FiredAtMs]; !ok && r.Status != "aborted" && r.Status != "panic" {
			return model.LedgerExport{}, fmt.Errorf("unexpected fire %s at %d", r.JobID, r.FiredAtMs)
		}
	}
	fires, dedup, err := store.CountFires()
	if err != nil {
		return model.LedgerExport{}, err
	}
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

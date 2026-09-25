package export

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"

	"github.com/terminus/feast-pit-join/internal/ledger"
	"github.com/terminus/feast-pit-join/internal/model"
	"github.com/terminus/feast-pit-join/internal/staging"
)

func BuildReport(stagingPath, dbPath, seed, scenario string) (model.ReportExport, error) {
	snap, err := staging.ReadSnapshot(stagingPath)
	if err != nil {
		return model.ReportExport{}, err
	}
	if err := staging.ValidateSeedScenario(snap, seed, scenario); err != nil {
		return model.ReportExport{}, err
	}
	store, err := ledger.Open(dbPath)
	if err != nil {
		return model.ReportExport{}, err
	}
	defer store.Close()
	runID, ok, err := store.LatestRun(seed, scenario)
	if err != nil || !ok {
		return model.ReportExport{}, err
	}
	parityOK, err := store.RunParityOK(runID)
	if err != nil {
		return model.ReportExport{}, err
	}
	sum, err := store.LoadSummary(runID)
	if err != nil {
		return model.ReportExport{}, err
	}
	reportSum := model.ReportSum{
		MismatchCount:       sum.MismatchCount,
		TTLFilteredCount:    sum.TTLFilteredCount,
		DuplicateTSResolved: sum.DuplicateTSResolved,
		AsOfTS:              sum.AsOfTSList,
	}
	digest := auditDigest(reportSum)
	return model.ReportExport{
		Seed: seed, Scenario: scenario, RunID: runID, ParityOK: parityOK,
		Summary: reportSum, AuditDigest: digest,
	}, nil
}

func WriteReport(path string, rep model.ReportExport) error {
	data, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o644)
}

func auditDigest(sum model.ReportSum) string {
	data, _ := json.Marshal(sum)
	h := sha256.Sum256(data)
	return hex.EncodeToString(h[:])
}

package export

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"sort"

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
	asOf := append([]int64(nil), sum.AsOfTSList...)
	sort.Slice(asOf, func(i, j int) bool { return asOf[i] < asOf[j] })
	reportSum := model.ReportSum{
		MismatchCount:       sum.MismatchCount,
		TTLFilteredCount:    sum.TTLFilteredCount,
		DuplicateTSResolved: sum.DuplicateTSResolved,
		AsOfTS:              asOf,
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
	text := canonicalJSON(sum)
	h := sha256.Sum256([]byte(text))
	return hex.EncodeToString(h[:])
}

func canonicalJSON(v any) string {
	switch t := v.(type) {
	case model.ReportSum:
		keys := []string{"as_of_ts", "duplicate_ts_resolved", "mismatch_count", "ttl_filtered_count"}
		parts := make([]string, 0, len(keys))
		asOfParts := make([]string, len(t.AsOfTS))
		for i, n := range t.AsOfTS {
			asOfParts[i] = jsonNum(n)
		}
		m := map[string]string{
			"as_of_ts":              "[" + joinComma(asOfParts) + "]",
			"duplicate_ts_resolved": jsonNum(int64(t.DuplicateTSResolved)),
			"mismatch_count":        jsonNum(int64(t.MismatchCount)),
			"ttl_filtered_count":    jsonNum(int64(t.TTLFilteredCount)),
		}
		for _, k := range keys {
			parts = append(parts, `"`+k+`":`+m[k])
		}
		return "{" + joinComma(parts) + "}"
	default:
		b, _ := json.Marshal(v)
		return string(b)
	}
}

func jsonNum(n int64) string {
	b, _ := json.Marshal(n)
	return string(b)
}

func joinComma(parts []string) string {
	if len(parts) == 0 {
		return ""
	}
	out := parts[0]
	for i := 1; i < len(parts); i++ {
		out += "," + parts[i]
	}
	return out
}

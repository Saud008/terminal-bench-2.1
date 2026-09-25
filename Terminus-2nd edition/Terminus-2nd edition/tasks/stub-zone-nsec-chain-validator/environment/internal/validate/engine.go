package validate

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"nsecval/internal/ingest"
	"nsecval/internal/model"
	"nsecval/internal/nsec"
	"nsecval/internal/proof"
	"nsecval/internal/stub"
)

const DefaultSnapshotPath = "/app/state/chain-snapshot.json"

type Result struct {
	Report model.Report
}

func Run(capturePath, reportPath, snapshotPath string) (Result, error) {
	cap, err := ingest.LoadCapture(capturePath)
	if err != nil {
		return Result{}, err
	}
	sha, err := ingest.MustSnapshot(snapshotPath, cap)
	if err != nil {
		return Result{}, err
	}
	chainOK := true
	if err := nsec.ValidateChain(cap.Zone, cap.Records); err != nil {
		chainOK = false
	}
	cache := stub.NewCache()
	cache.ObserveSerial(cap.SOASerial)
	walker := proof.Walker{
		Zone:    cap.Zone,
		Records: cap.Records,
		Params:  cap.NSEC3Params,
		Cache:   cache,
	}
	results := make([]model.QueryResult, 0, len(cap.Queries))
	for _, q := range cap.Queries {
		if q.SOASerial != 0 {
			cache.ObserveSerial(q.SOASerial)
		}
		res, _, err := walker.ValidateQuery(q)
		if err != nil {
			return Result{}, err
		}
		results = append(results, res)
	}
	rep := model.Report{
		Zone:        cap.Zone,
		SOASerial:   cap.SOASerial,
		ChainValid:  chainOK,
		Queries:     results,
		CacheHits:   cache.Hits(),
		SnapshotSHA: sha,
	}
	if err := writeReport(reportPath, rep); err != nil {
		return Result{}, err
	}
	return Result{Report: rep}, nil
}

func writeReport(path string, rep model.Report) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}

func IngestOnly(capturePath, snapshotPath string) (string, error) {
	cap, err := ingest.LoadCapture(capturePath)
	if err != nil {
		return "", err
	}
	sha, err := ingest.MustSnapshot(snapshotPath, cap)
	if err != nil {
		return "", fmt.Errorf("ingest: %w", err)
	}
	return sha, nil
}

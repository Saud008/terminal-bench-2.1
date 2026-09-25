package ledger

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"

	"github.com/terminus/mlflow-provenance-curator/internal/model"
)

func Open(path string) (*sql.DB, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	schema := `
CREATE TABLE IF NOT EXISTS curation_runs (
  run_id INTEGER PRIMARY KEY AUTOINCREMENT,
  seed TEXT NOT NULL,
  scenario TEXT NOT NULL,
  focus_run_id TEXT NOT NULL,
  ingest_seq INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS provenance_summary (
  run_id INTEGER PRIMARY KEY,
  binding_ok INTEGER NOT NULL,
  epoch_monotonic_ok INTEGER NOT NULL,
  lineage_depth INTEGER NOT NULL,
  artifact_count INTEGER NOT NULL,
  lineage_chain TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES curation_runs(run_id)
);
`
	if _, err := db.Exec(schema); err != nil {
		db.Close()
		return nil, err
	}
	return db, nil
}

func ReplaceRun(db *sql.DB, seed, scenario, focus string, ingestSeq int64, summary model.SummaryBlock, chain []string) (int64, error) {
	if _, err := db.Exec(`DELETE FROM provenance_summary`); err != nil {
		return 0, err
	}
	if _, err := db.Exec(`DELETE FROM curation_runs`); err != nil {
		return 0, err
	}
	chainJSON, err := json.Marshal(chain)
	if err != nil {
		return 0, err
	}
	res, err := db.Exec(
		`INSERT INTO curation_runs(seed, scenario, focus_run_id, ingest_seq) VALUES(?,?,?,?)`,
		seed, scenario, focus, ingestSeq,
	)
	if err != nil {
		return 0, err
	}
	runID, err := res.LastInsertId()
	if err != nil {
		return 0, err
	}
	_, err = db.Exec(
		`INSERT INTO provenance_summary(run_id, binding_ok, epoch_monotonic_ok, lineage_depth, artifact_count, lineage_chain)
		 VALUES(?,?,?,?,?,?)`,
		runID, boolInt(summary.BindingOK), boolInt(summary.EpochMonotonicOK), summary.LineageDepth, summary.ArtifactCount, string(chainJSON),
	)
	if err != nil {
		return 0, err
	}
	return runID, nil
}

func LatestSummary(db *sql.DB, seed, scenario string) (int64, model.SummaryBlock, []string, error) {
	row := db.QueryRow(`
SELECT r.run_id, s.binding_ok, s.epoch_monotonic_ok, s.lineage_depth, s.artifact_count, s.lineage_chain
FROM curation_runs r
JOIN provenance_summary s ON s.run_id = r.run_id
WHERE r.seed = ? AND r.scenario = ?
ORDER BY r.run_id DESC LIMIT 1`, seed, scenario)
	var runID int64
	var binding, epoch, depth, count int
	var chainRaw string
	if err := row.Scan(&runID, &binding, &epoch, &depth, &count, &chainRaw); err != nil {
		return 0, model.SummaryBlock{}, nil, fmt.Errorf("no curation run: %w", err)
	}
	var chain []string
	if err := json.Unmarshal([]byte(chainRaw), &chain); err != nil {
		return 0, model.SummaryBlock{}, nil, err
	}
	return runID, model.SummaryBlock{
		BindingOK:        binding == 1,
		EpochMonotonicOK: epoch == 1,
		LineageDepth:     depth,
		ArtifactCount:    count,
	}, chain, nil
}

func boolInt(v bool) int {
	if v {
		return 1
	}
	return 0
}

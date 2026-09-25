package journal

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"

	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"
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
CREATE TABLE IF NOT EXISTS atlas_runs (
  run_id INTEGER PRIMARY KEY AUTOINCREMENT,
  seed TEXT NOT NULL,
  scenario TEXT NOT NULL,
  focus_alloc_id TEXT NOT NULL,
  load_seq INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS atlas_summary (
  run_id INTEGER PRIMARY KEY,
  active_alloc_count INTEGER NOT NULL,
  stale_suppressed INTEGER NOT NULL,
  drain_excluded INTEGER NOT NULL,
  reschedule_total INTEGER NOT NULL,
  volume_join_count INTEGER NOT NULL,
  spread_penalty_total INTEGER NOT NULL,
  constraint_pass_ok INTEGER NOT NULL,
  affinity_monotone_ok INTEGER NOT NULL,
  placements_json TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES atlas_runs(run_id)
);
`
	if _, err := db.Exec(schema); err != nil {
		db.Close()
		return nil, err
	}
	return db, nil
}

func ReplaceRun(db *sql.DB, seed, scenario, focus string, loadSeq int64, summary model.SummaryBlock, placements []model.PlacementRow) (int64, error) {
	if _, err := db.Exec(`DELETE FROM atlas_summary`); err != nil {
		return 0, err
	}
	if _, err := db.Exec(`DELETE FROM atlas_runs`); err != nil {
		return 0, err
	}
	placementsJSON, err := json.Marshal(placements)
	if err != nil {
		return 0, err
	}
	res, err := db.Exec(
		`INSERT INTO atlas_runs(seed, scenario, focus_alloc_id, load_seq) VALUES(?,?,?,?)`,
		seed, scenario, focus, loadSeq,
	)
	if err != nil {
		return 0, err
	}
	runID, err := res.LastInsertId()
	if err != nil {
		return 0, err
	}
	_, err = db.Exec(
		`INSERT INTO atlas_summary(run_id, active_alloc_count, stale_suppressed, drain_excluded, reschedule_total, volume_join_count, spread_penalty_total, constraint_pass_ok, affinity_monotone_ok, placements_json)
		 VALUES(?,?,?,?,?,?,?,?,?,?)`,
		runID,
		summary.ActiveAllocCount,
		summary.StaleSuppressed,
		summary.DrainExcluded,
		summary.RescheduleTotal,
		summary.VolumeJoinCount,
		summary.SpreadPenaltyTotal,
		boolInt(summary.ConstraintPassOK),
		boolInt(summary.AffinityMonotoneOK),
		string(placementsJSON),
	)
	if err != nil {
		return 0, err
	}
	return runID, nil
}

func LatestSummary(db *sql.DB, seed, scenario string) (int64, model.SummaryBlock, []model.PlacementRow, error) {
	row := db.QueryRow(`
SELECT r.run_id, s.active_alloc_count, s.stale_suppressed, s.drain_excluded, s.reschedule_total, s.volume_join_count,
       s.spread_penalty_total, s.constraint_pass_ok, s.affinity_monotone_ok, s.placements_json
FROM atlas_runs r
JOIN atlas_summary s ON s.run_id = r.run_id
WHERE r.seed = ? AND r.scenario = ?
ORDER BY r.run_id DESC LIMIT 1`, seed, scenario)
	var runID int64
	var active, stale, drain, reschedule, joins, spreadPen, constraintOK, affinityOK int
	var placementsRaw string
	if err := row.Scan(&runID, &active, &stale, &drain, &reschedule, &joins, &spreadPen, &constraintOK, &affinityOK, &placementsRaw); err != nil {
		return 0, model.SummaryBlock{}, nil, fmt.Errorf("no atlas run: %w", err)
	}
	var placements []model.PlacementRow
	if err := json.Unmarshal([]byte(placementsRaw), &placements); err != nil {
		return 0, model.SummaryBlock{}, nil, err
	}
	return runID, model.SummaryBlock{
		ActiveAllocCount:   active,
		StaleSuppressed:    stale,
		DrainExcluded:      drain,
		RescheduleTotal:    reschedule,
		VolumeJoinCount:    joins,
		SpreadPenaltyTotal: spreadPen,
		ConstraintPassOK:   constraintOK == 1,
		AffinityMonotoneOK: affinityOK == 1,
	}, placements, nil
}

func boolInt(v bool) int {
	if v {
		return 1
	}
	return 0
}

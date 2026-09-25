package yardsql

import (
	"database/sql"
	"fmt"

	_ "modernc.org/sqlite"

	"github.com/terminus/demurctl/internal/model"
)

const YardDB = "/app/state/yard.db"

func Open(path string) (*sql.DB, error) {
	return sql.Open("sqlite", path)
}

func InitSchema(db *sql.DB) error {
	_, err := db.Exec(`
		CREATE TABLE IF NOT EXISTS yard_meta (
			scenario_id TEXT,
			billing_through TEXT,
			loaded_at TEXT
		);
		CREATE TABLE IF NOT EXISTS containers (
			container_id TEXT PRIMARY KEY,
			carrier_id TEXT
		);
		CREATE TABLE IF NOT EXISTS gate_events (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			container_id TEXT,
			event TEXT,
			ts TEXT
		);
		CREATE TABLE IF NOT EXISTS contracts (
			container_id TEXT PRIMARY KEY,
			free_days INTEGER,
			currency TEXT
		);
		CREATE TABLE IF NOT EXISTS holds (
			hold_id TEXT PRIMARY KEY,
			container_id TEXT,
			code TEXT,
			start_date TEXT,
			end_date TEXT
		);
		CREATE TABLE IF NOT EXISTS closures (
			closure_date TEXT PRIMARY KEY,
			reason TEXT
		);
		CREATE TABLE IF NOT EXISTS tariffs (
			carrier_id TEXT PRIMARY KEY,
			tier1_days INTEGER,
			tier1_rate_cents INTEGER,
			tier2_rate_cents INTEGER,
			tier3_rate_cents INTEGER
		);
		CREATE TABLE IF NOT EXISTS staged_dwell (
			container_id TEXT PRIMARY KEY,
			eligible_days INTEGER,
			free_days_used INTEGER,
			demurrage_days INTEGER,
			tier1_days INTEGER,
			tier2_days INTEGER,
			tier3_days INTEGER,
			total_cents INTEGER,
			active_hold TEXT,
			currency TEXT
		);
	`)
	return err
}

func ClearYard(db *sql.DB) error {
	tables := []string{
		"yard_meta", "containers", "gate_events", "contracts",
		"holds", "closures", "tariffs", "staged_dwell",
	}
	for _, t := range tables {
		if _, err := db.Exec("DELETE FROM " + t); err != nil {
			return err
		}
	}
	return nil
}

func InsertScenario(db *sql.DB, sc model.Scenario) error {
	if _, err := db.Exec(
		"INSERT INTO yard_meta (scenario_id, billing_through, loaded_at) VALUES (?,?,?)",
		sc.ScenarioID, sc.BillingThrough, "",
	); err != nil {
		return err
	}
	for _, c := range sc.Containers {
		if _, err := db.Exec(
			"INSERT INTO containers (container_id, carrier_id) VALUES (?,?)",
			c.ContainerID, c.CarrierID,
		); err != nil {
			return err
		}
	}
	for _, e := range sc.GateEvents {
		if _, err := db.Exec(
			"INSERT INTO gate_events (container_id, event, ts) VALUES (?,?,?)",
			e.ContainerID, e.Event, e.Ts,
		); err != nil {
			return err
		}
	}
	for _, c := range sc.Contracts {
		if _, err := db.Exec(
			"INSERT INTO contracts (container_id, free_days, currency) VALUES (?,?,?)",
			c.ContainerID, c.FreeDays, c.Currency,
		); err != nil {
			return err
		}
	}
	for _, h := range sc.Holds {
		if _, err := db.Exec(
			"INSERT INTO holds (hold_id, container_id, code, start_date, end_date) VALUES (?,?,?,?,?)",
			h.HoldID, h.ContainerID, h.Code, h.Start, h.End,
		); err != nil {
			return err
		}
	}
	for _, cl := range sc.Closures {
		if _, err := db.Exec(
			"INSERT INTO closures (closure_date, reason) VALUES (?,?)",
			cl.Date, cl.Reason,
		); err != nil {
			return err
		}
	}
	for _, t := range sc.Tariffs {
		if _, err := db.Exec(
			"INSERT INTO tariffs (carrier_id, tier1_days, tier1_rate_cents, tier2_rate_cents, tier3_rate_cents) VALUES (?,?,?,?,?)",
			t.CarrierID, t.Tier1Days, t.Tier1RateCents, t.Tier2RateCents, t.Tier3RateCents,
		); err != nil {
			return err
		}
	}
	return nil
}

func ReadMeta(db *sql.DB) (string, string, error) {
	var scenarioID, billingThrough string
	err := db.QueryRow("SELECT scenario_id, billing_through FROM yard_meta LIMIT 1").Scan(&scenarioID, &billingThrough)
	return scenarioID, billingThrough, err
}

func ReadContainers(db *sql.DB) ([]model.Container, error) {
	rows, err := db.Query("SELECT container_id, carrier_id FROM containers ORDER BY container_id")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.Container
	for rows.Next() {
		var c model.Container
		if err := rows.Scan(&c.ContainerID, &c.CarrierID); err != nil {
			return nil, err
		}
		out = append(out, c)
	}
	return out, rows.Err()
}

func ReadGateEvents(db *sql.DB, containerID string) ([]model.GateEvent, error) {
	rows, err := db.Query(
		"SELECT container_id, event, ts FROM gate_events WHERE container_id = ? ORDER BY id",
		containerID,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.GateEvent
	for rows.Next() {
		var e model.GateEvent
		if err := rows.Scan(&e.ContainerID, &e.Event, &e.Ts); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, rows.Err()
}

func ReadContract(db *sql.DB, containerID string) (model.Contract, error) {
	var c model.Contract
	err := db.QueryRow(
		"SELECT container_id, free_days, currency FROM contracts WHERE container_id = ?",
		containerID,
	).Scan(&c.ContainerID, &c.FreeDays, &c.Currency)
	return c, err
}

func ReadHolds(db *sql.DB, containerID string) ([]model.Hold, error) {
	rows, err := db.Query(
		"SELECT hold_id, container_id, code, start_date, end_date FROM holds WHERE container_id = ?",
		containerID,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.Hold
	for rows.Next() {
		var h model.Hold
		if err := rows.Scan(&h.HoldID, &h.ContainerID, &h.Code, &h.Start, &h.End); err != nil {
			return nil, err
		}
		out = append(out, h)
	}
	return out, rows.Err()
}

func ReadClosures(db *sql.DB) ([]model.Closure, error) {
	rows, err := db.Query("SELECT closure_date, reason FROM closures")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.Closure
	for rows.Next() {
		var c model.Closure
		if err := rows.Scan(&c.Date, &c.Reason); err != nil {
			return nil, err
		}
		out = append(out, c)
	}
	return out, rows.Err()
}

func ReadTariff(db *sql.DB, carrierID string) (model.Tariff, error) {
	var t model.Tariff
	err := db.QueryRow(
		"SELECT carrier_id, tier1_days, tier1_rate_cents, tier2_rate_cents, tier3_rate_cents FROM tariffs WHERE carrier_id = ?",
		carrierID,
	).Scan(&t.CarrierID, &t.Tier1Days, &t.Tier1RateCents, &t.Tier2RateCents, &t.Tier3RateCents)
	return t, err
}

func UpsertStagedDwell(db *sql.DB, d model.StagedDwell) error {
	_, err := db.Exec(`
		INSERT INTO staged_dwell (
			container_id, eligible_days, free_days_used, demurrage_days,
			tier1_days, tier2_days, tier3_days, total_cents, active_hold, currency
		) VALUES (?,?,?,?,?,?,?,?,?,?)
		ON CONFLICT(container_id) DO UPDATE SET
			eligible_days=excluded.eligible_days,
			free_days_used=excluded.free_days_used,
			demurrage_days=excluded.demurrage_days,
			tier1_days=excluded.tier1_days,
			tier2_days=excluded.tier2_days,
			tier3_days=excluded.tier3_days,
			total_cents=excluded.total_cents,
			active_hold=excluded.active_hold,
			currency=excluded.currency
	`, d.ContainerID, d.EligibleDays, d.FreeDaysUsed, d.DemurrageDays,
		d.Tier1Days, d.Tier2Days, d.Tier3Days, d.TotalCents, d.ActiveHold, d.Currency)
	return err
}

func ReadStagedDwell(db *sql.DB) ([]model.StagedDwell, error) {
	rows, err := db.Query(`
		SELECT container_id, eligible_days, free_days_used, demurrage_days,
			tier1_days, tier2_days, tier3_days, total_cents, active_hold, currency
		FROM staged_dwell ORDER BY container_id
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.StagedDwell
	for rows.Next() {
		var d model.StagedDwell
		if err := rows.Scan(
			&d.ContainerID, &d.EligibleDays, &d.FreeDaysUsed, &d.DemurrageDays,
			&d.Tier1Days, &d.Tier2Days, &d.Tier3Days, &d.TotalCents, &d.ActiveHold, &d.Currency,
		); err != nil {
			return nil, err
		}
		out = append(out, d)
	}
	return out, rows.Err()
}

func MustReadStaged(db *sql.DB) ([]model.StagedDwell, error) {
	out, err := ReadStagedDwell(db)
	if err != nil {
		return nil, fmt.Errorf("read staged_dwell: %w", err)
	}
	if len(out) == 0 {
		return nil, fmt.Errorf("staged_dwell empty")
	}
	return out, nil
}

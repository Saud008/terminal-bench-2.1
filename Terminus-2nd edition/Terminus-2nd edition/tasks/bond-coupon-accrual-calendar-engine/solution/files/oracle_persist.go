package persist

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"

	"github.com/terminus/bondacc/internal/model"
)

const dbPath = "/app/state/accrual.db"
const passPath = "/app/state/accrual-pass.json"

type PassGate struct {
	Scenario    string `json:"scenario"`
	AccrualPass int    `json:"accrual_pass"`
}

func Open() (*sql.DB, error) {
	if err := os.MkdirAll(filepath.Dir(dbPath), 0o755); err != nil {
		return nil, err
	}
	return sql.Open("sqlite", "file:"+dbPath+"?cache=shared&_pragma=busy_timeout(10000)")
}

func InitSchema(db *sql.DB) error {
	_, err := db.Exec(`CREATE TABLE IF NOT EXISTS bonds (
		isin TEXT PRIMARY KEY, face_cents INTEGER, coupon_bps INTEGER, frequency INTEGER,
		day_count TEXT, ex_days INTEGER, calendar_id TEXT, issue_date TEXT, maturity_date TEXT
	)`)
	if err != nil {
		return err
	}
	_, err = db.Exec(`CREATE TABLE IF NOT EXISTS trades (
		trade_id TEXT PRIMARY KEY, isin TEXT, trade_date TEXT, settle_lag_bdays INTEGER
	)`)
	if err != nil {
		return err
	}
	_, err = db.Exec(`CREATE TABLE IF NOT EXISTS accruals (
		trade_id TEXT PRIMARY KEY, isin TEXT, period_start TEXT, period_end TEXT,
		settlement_date TEXT, accrued_cents INTEGER, ex_coupon INTEGER
	)`)
	return err
}

func WritePass(scenario string, pass int) error {
	g := PassGate{Scenario: scenario, AccrualPass: pass}
	raw, _ := json.Marshal(g)
	return os.WriteFile(passPath, raw, 0o644)
}

func ReadPass() (PassGate, error) {
	raw, err := os.ReadFile(passPath)
	if err != nil {
		return PassGate{}, err
	}
	var g PassGate
	return g, json.Unmarshal(raw, &g)
}

func UpsertBond(db *sql.DB, b model.Bond) error {
	_, err := db.Exec(`INSERT OR REPLACE INTO bonds VALUES (?,?,?,?,?,?,?,?,?)`,
		b.ISIN, b.FaceCents, b.CouponBPS, b.Frequency, b.DayCount, b.ExDays, b.CalendarID, b.IssueDate, b.MaturityDate)
	return err
}

func UpsertTrade(db *sql.DB, t model.Trade) error {
	_, err := db.Exec(`INSERT OR REPLACE INTO trades VALUES (?,?,?,?)`,
		t.TradeID, t.ISIN, t.TradeDate, t.SettleLag)
	return err
}

func UpsertAccrual(db *sql.DB, r model.AccrualRow) error {
	ex := 0
	if r.ExCoupon {
		ex = 1
	}
	_, err := db.Exec(`INSERT OR REPLACE INTO accruals VALUES (?,?,?,?,?,?,?)`,
		r.TradeID, r.ISIN, r.PeriodStart, r.PeriodEnd, r.SettlementDate, r.AccruedCents, ex)
	return err
}

func RequirePositivePass(scenario string) error {
	g, err := ReadPass()
	if err != nil {
		return err
	}
	if g.Scenario != scenario {
		return fmt.Errorf("pass gate scenario mismatch")
	}
	if g.AccrualPass < 2 {
		return fmt.Errorf("accrual_pass not advanced")
	}
	return nil
}

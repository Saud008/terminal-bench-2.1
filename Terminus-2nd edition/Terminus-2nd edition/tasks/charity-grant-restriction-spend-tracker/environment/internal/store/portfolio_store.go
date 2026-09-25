package store

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"

	"github.com/terminus/grantctl/internal/model"
)

const dbPath = "/app/state/grant-portfolio.db"

func Open() (*sql.DB, error) {
	if err := os.MkdirAll(filepath.Dir(dbPath), 0o755); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", dbPath+"?_pragma=busy_timeout(5000)")
	if err != nil {
		return nil, err
	}
	if err := createSchema(db); err != nil {
		_ = db.Close()
		return nil, err
	}
	return db, nil
}

func createSchema(db *sql.DB) error {
	stmts := []string{
		`CREATE TABLE IF NOT EXISTS grants (
			grant_id TEXT PRIMARY KEY,
			project TEXT NOT NULL,
			restriction_path TEXT NOT NULL,
			allowed_categories_json TEXT NOT NULL,
			ceiling_cents INTEGER NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS project_aliases (
			alias TEXT PRIMARY KEY,
			alias_of TEXT NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS expenses (
			expense_id TEXT PRIMARY KEY,
			project TEXT NOT NULL,
			category_path TEXT NOT NULL,
			category TEXT NOT NULL,
			expense_date TEXT NOT NULL,
			amount_cents INTEGER NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS amendments (
			amendment_id TEXT PRIMARY KEY,
			grant_id TEXT NOT NULL,
			effective_date TEXT NOT NULL,
			delta_cents INTEGER NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS staged_balances (
			grant_id TEXT PRIMARY KEY,
			spent_cents INTEGER NOT NULL,
			remaining_cents INTEGER NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS staged_rejections (
			expense_id TEXT PRIMARY KEY,
			reason TEXT NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS published_spend (
			run_id TEXT NOT NULL,
			grant_id TEXT NOT NULL,
			spent_cents INTEGER NOT NULL
		)`,
	}
	for _, stmt := range stmts {
		if _, err := db.Exec(stmt); err != nil {
			return err
		}
	}
	return nil
}

func ResetScenarioRows(db *sql.DB) error {
	for _, tbl := range []string{"grants", "project_aliases", "expenses", "amendments", "staged_balances", "staged_rejections"} {
		if _, err := db.Exec(fmt.Sprintf("DELETE FROM %s", tbl)); err != nil {
			return err
		}
	}
	return nil
}

func InsertScenario(db *sql.DB, scenario model.Scenario) error {
	for _, g := range scenario.Grants {
		b, _ := json.Marshal(g.AllowedCategories)
		if _, err := db.Exec(
			`INSERT INTO grants(grant_id, project, restriction_path, allowed_categories_json, ceiling_cents)
			 VALUES(?, ?, ?, ?, ?)`,
			g.GrantID, g.Project, g.RestrictionPath, string(b), g.CeilingCents,
		); err != nil {
			return err
		}
	}
	for _, a := range scenario.ProjectAliases {
		if _, err := db.Exec(
			`INSERT INTO project_aliases(alias, alias_of) VALUES(?, ?)`,
			a.Alias, a.AliasOf,
		); err != nil {
			return err
		}
	}
	for _, e := range scenario.Expenses {
		if _, err := db.Exec(
			`INSERT INTO expenses(expense_id, project, category_path, category, expense_date, amount_cents)
			 VALUES(?, ?, ?, ?, ?, ?)`,
			e.ExpenseID, e.Project, e.CategoryPath, e.Category, e.ExpenseDate, e.AmountCents,
		); err != nil {
			return err
		}
	}
	for _, m := range scenario.Amendments {
		if _, err := db.Exec(
			`INSERT INTO amendments(amendment_id, grant_id, effective_date, delta_cents)
			 VALUES(?, ?, ?, ?)`,
			m.AmendmentID, m.GrantID, m.EffectiveDate, m.DeltaCents,
		); err != nil {
			return err
		}
	}
	return nil
}

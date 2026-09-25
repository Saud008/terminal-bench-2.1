package store

import (
    "database/sql"
    "fmt"
    "os"

    _ "modernc.org/sqlite"
)

const DBPath = "/app/state/billing.db"

func Open() (*sql.DB, error) {
    if err := os.MkdirAll("/app/state", 0o755); err != nil {
        return nil, err
    }
    db, err := sql.Open("sqlite", DBPath)
    if err != nil {
        return nil, err
    }
    if err := migrate(db); err != nil {
        db.Close()
        return nil, err
    }
    return db, nil
}

func migrate(db *sql.DB) error {
    stmts := []string{
        `CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)`,
        `CREATE TABLE IF NOT EXISTS plans (plan_id TEXT PRIMARY KEY, monthly_cents INTEGER, included_units INTEGER, overage_cents INTEGER)`,
        `CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT, event_date TEXT, from_plan TEXT, to_plan TEXT, units INTEGER)`,
        `CREATE TABLE IF NOT EXISTS coupons (coupon_id TEXT PRIMARY KEY, precedence INTEGER, kind TEXT, value INTEGER, stackable INTEGER)`,
        `CREATE TABLE IF NOT EXISTS anchor_shifts (effective_date TEXT, new_anchor_day INTEGER)`,
        `CREATE TABLE IF NOT EXISTS segments (segment_index INTEGER PRIMARY KEY, plan_id TEXT, window_start TEXT, window_end TEXT, segment_days INTEGER, base_cents INTEGER)`,
        `CREATE TABLE IF NOT EXISTS ledger (id INTEGER PRIMARY KEY AUTOINCREMENT, line_kind TEXT, segment_index INTEGER, amount_cents INTEGER, pass_num INTEGER)`,
    }
    for _, s := range stmts {
        if _, err := db.Exec(s); err != nil {
            return fmt.Errorf("migrate: %w", err)
        }
    }
    return nil
}

func SetMeta(db *sql.DB, key, value string) error {
    _, err := db.Exec(`INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value`, key, value)
    return err
}

func GetMeta(db *sql.DB, key string) (string, error) {
    var v string
    err := db.QueryRow(`SELECT value FROM meta WHERE key=?`, key).Scan(&v)
    return v, err
}

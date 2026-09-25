package store

import (
    "database/sql"
    "fmt"
    "os"

    _ "modernc.org/sqlite"
)

const DBPath = "/app/state/settlement.db"

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
        `CREATE TABLE IF NOT EXISTS lots (lot_id TEXT PRIMARY KEY, reserve_cents INTEGER, withdrawn INTEGER, premium_tier TEXT)`,
        `CREATE TABLE IF NOT EXISTS bids (id INTEGER PRIMARY KEY AUTOINCREMENT, lot_id TEXT, bidder_id TEXT, amount_cents INTEGER, bid_seq INTEGER, bid_ts TEXT)`,
        `CREATE TABLE IF NOT EXISTS deposits (bidder_id TEXT PRIMARY KEY, deposit_cents INTEGER)`,
        `CREATE TABLE IF NOT EXISTS adjustments (lot_id TEXT, bidder_id TEXT, adjustment_cents INTEGER)`,
        `CREATE TABLE IF NOT EXISTS awards (lot_id TEXT PRIMARY KEY, status TEXT, bidder_id TEXT, hammer_cents INTEGER)`,
        `CREATE TABLE IF NOT EXISTS ledger (id INTEGER PRIMARY KEY AUTOINCREMENT, lot_id TEXT, bidder_id TEXT, line_kind TEXT, amount_cents INTEGER, pass_num INTEGER)`,
        `CREATE TABLE IF NOT EXISTS deposit_applied (bidder_id TEXT PRIMARY KEY, applied_cents INTEGER)`,
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

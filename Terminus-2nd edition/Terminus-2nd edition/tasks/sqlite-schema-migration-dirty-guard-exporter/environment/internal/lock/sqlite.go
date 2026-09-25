package lock

import (
	"database/sql"
	"os"
	"strconv"
	"time"
)

// WithExclusive runs fn while holding the schema_migrations export lock.
func WithExclusive(db *sql.DB, fn func() error) error {
	if _, err := db.Exec(`BEGIN DEFERRED`); err != nil {
		return err
	}
	if hold := os.Getenv("TB3_EXPORT_HOLD_MS"); hold != "" {
		if ms, err := strconv.Atoi(hold); err == nil && ms > 0 {
			time.Sleep(time.Duration(ms) * time.Millisecond)
		}
	}
	if err := fn(); err != nil {
		_, _ = db.Exec(`ROLLBACK`)
		return err
	}
	_, err := db.Exec(`COMMIT`)
	return err
}

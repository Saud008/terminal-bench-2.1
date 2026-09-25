package apply

import (
	"database/sql"
	"fmt"
	"sort"

	"github.com/terminus/sqlitemigrate/internal/lock"
	"github.com/terminus/sqlitemigrate/internal/staging"
	"github.com/terminus/sqlitemigrate/internal/types"
)

const DefaultDBPath = "/app/state/migrations.db"

// ApplyJournal replays migration journal entries against SQLite.
func ApplyJournal(db *sql.DB, events []types.JournalEntry, stagePath string) error {
	sort.SliceStable(events, func(i, j int) bool { return events[i].Seq < events[j].Seq })
	if err := ensureSchema(db); err != nil {
		return err
	}
	st := staging.NewEmpty()
	for _, ev := range events {
		if ev.Direction == "up" {
			dirty, err := readDirty(db)
			if err != nil {
				return err
			}
			if dirty {
				return fmt.Errorf("dirty guard: cannot apply up while dirty at seq %d", ev.Seq)
			}
			if err := writeVersion(db, ev.Version); err != nil {
				return err
			}
			if err := execStatements(db, ev.SQL); err != nil {
				_ = writeDirty(db, true)
				_ = writeDirty(db, false)
				st.FailedDownRollbacks += countDownRollbacks(events, ev.Seq, ev.Version)
				st.Dirty = false
				st.Version, _ = readVersion(db)
				st.LastSeq = ev.Seq
				st.AppliedSteps++
				_ = staging.Save(stagePath, st)
				return err
			}
			if err := appendVersionLog(db, ev.Version); err != nil {
				return err
			}
			if err := writeDirty(db, false); err != nil {
				return err
			}
			st.Version = ev.Version
			st.Dirty = false
		} else if ev.Direction == "down" {
			if err := execStatements(db, ev.SQL); err != nil {
				return err
			}
			if err := writeVersion(db, ev.Version-1); err != nil {
				return err
			}
			st.Version = ev.Version - 1
		} else {
			return fmt.Errorf("unknown direction %q at seq %d", ev.Direction, ev.Seq)
		}
		st.LastSeq = ev.Seq
		st.AppliedSteps++
	}
	return staging.Save(stagePath, st)
}

func ensureSchema(db *sql.DB) error {
	stmts := []string{
		`CREATE TABLE IF NOT EXISTS schema_migrations (
			version INTEGER NOT NULL,
			dirty INTEGER NOT NULL DEFAULT 0
		)`,
		`CREATE TABLE IF NOT EXISTS version_log (
			version INTEGER NOT NULL
		)`,
	}
	for _, s := range stmts {
		if _, err := db.Exec(s); err != nil {
			return err
		}
	}
	return nil
}

func execStatements(db *sql.DB, sqlText string) error {
	for _, stmt := range SplitStatements(sqlText) {
		if _, err := db.Exec(stmt); err != nil {
			return err
		}
	}
	return nil
}

func appendVersionLog(db *sql.DB, version int) error {
	_, err := db.Exec(`INSERT INTO version_log (version) VALUES (?)`, version)
	return err
}

func readVersion(db *sql.DB) (int, error) {
	var v int
	err := db.QueryRow(`SELECT version FROM schema_migrations ORDER BY rowid DESC LIMIT 1`).Scan(&v)
	if err == sql.ErrNoRows {
		return 0, nil
	}
	return v, err
}

func readDirty(db *sql.DB) (bool, error) {
	var d int
	err := db.QueryRow(`SELECT dirty FROM schema_migrations ORDER BY rowid DESC LIMIT 1`).Scan(&d)
	if err == sql.ErrNoRows {
		return false, nil
	}
	return d != 0, err
}

func writeVersion(db *sql.DB, version int) error {
	_, err := db.Exec(`DELETE FROM schema_migrations`)
	if err != nil {
		return err
	}
	_, err = db.Exec(`INSERT INTO schema_migrations (version, dirty) VALUES (?, 0)`, version)
	return err
}

func writeDirty(db *sql.DB, dirty bool) error {
	v, err := readVersion(db)
	if err != nil {
		return err
	}
	d := 0
	if dirty {
		d = 1
	}
	_, err = db.Exec(`DELETE FROM schema_migrations`)
	if err != nil {
		return err
	}
	_, err = db.Exec(`INSERT INTO schema_migrations (version, dirty) VALUES (?, ?)`, v, d)
	return err
}

func countDownRollbacks(events []types.JournalEntry, failedSeq, version int) int {
	n := 0
	for _, ev := range events {
		if ev.Seq > failedSeq && ev.Direction == "down" && ev.Version == version {
			n++
		}
	}
	return n
}

// OpenDB opens the SQLite database used by migratectl.
func OpenDB(path string) (*sql.DB, error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	return db, nil
}

// WithLock runs fn under the migration lock policy.
func WithLock(db *sql.DB, fn func() error) error {
	return lock.WithExclusive(db, fn)
}

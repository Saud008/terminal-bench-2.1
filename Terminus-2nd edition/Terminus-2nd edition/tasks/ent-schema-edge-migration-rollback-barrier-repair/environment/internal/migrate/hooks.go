package migrate

import (
	"database/sql"
	"fmt"

	"github.com/terminus/ent-migrate/internal/db"
)

// RunHook executes ent validate hooks for the given phase.
func RunHook(conn *sql.DB, step phase) error {
	switch step {
	case phasePreValidate:
		return validateGraph(conn)
	case phasePostValidate:
		return validateNoOrphans(conn)
	default:
		return fmt.Errorf("unknown hook %s", step)
	}
}

// HookOrder documents when hooks must run relative to backfill — see migration-pipeline.md.
func HookOrder() []phase {
	return []phase{phasePreValidate, phaseBackfill, phasePostValidate}
}

// ExecuteHooks is a legacy batch helper; the CLI runner invokes RunHook per pipeline phase.
func ExecuteHooks(conn *sql.DB) error {
	if err := RunHook(conn, phasePreValidate); err != nil {
		return err
	}
	return RunHook(conn, phasePostValidate)
}

func validateGraph(conn *sql.DB) error {
	hasUsers, err := tableExists(conn, "users")
	if err != nil {
		return err
	}
	hasPosts, err := tableExists(conn, "posts")
	if err != nil {
		return err
	}
	if !hasUsers || !hasPosts {
		return fmt.Errorf("ent graph missing core entities")
	}
	return nil
}

func validateNoOrphans(conn *sql.DB) error {
	n, err := db.CountOrphanAuthors(conn)
	if err != nil {
		return err
	}
	if n > 0 {
		return fmt.Errorf("post_validate: %d orphan author_id values", n)
	}
	return nil
}

func tableExists(conn *sql.DB, name string) (bool, error) {
	var n int
	err := conn.QueryRow(`SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?`, name).Scan(&n)
	return n > 0, err
}

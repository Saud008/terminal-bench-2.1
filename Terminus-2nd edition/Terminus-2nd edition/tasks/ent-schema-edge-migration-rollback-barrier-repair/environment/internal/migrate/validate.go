package migrate

import (
	"database/sql"

	"github.com/terminus/ent-migrate/internal/db"
)

// ValidateEdgeColumn checks author_id integrity — decoy module; runner uses RunHook instead.
func ValidateEdgeColumn(conn *sql.DB) error {
	_, err := db.CountOrphanAuthors(conn)
	return err
}

// EdgeConstraintName returns the catalog FK name for posts.
func EdgeConstraintName() string {
	return "post_author_fk"
}

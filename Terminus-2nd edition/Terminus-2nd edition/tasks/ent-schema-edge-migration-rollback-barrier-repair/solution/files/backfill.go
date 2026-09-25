package migrate

import (
	"database/sql"
)

// BackfillAuthor copies user_ref into author_id for posts.
func BackfillAuthor(conn *sql.DB) error {
	_, err := conn.Exec(`
UPDATE posts
SET author_id = CAST(substr(user_ref, 3) AS INTEGER)
WHERE author_id IS NULL AND user_ref LIKE 'u:%';
UPDATE posts
SET author_id = CAST(user_ref AS INTEGER)
WHERE author_id IS NULL
  AND user_ref GLOB '[0-9]*'
  AND user_ref NOT GLOB '*[^0-9]*'
`)
	return err
}

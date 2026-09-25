package migrate

import (
	"database/sql"
	"fmt"
)

const edgeTriggerSQL = `CREATE TRIGGER IF NOT EXISTS trg_post_author_edge
BEFORE INSERT ON posts
FOR EACH ROW
WHEN NEW.author_id IS NOT NULL AND NEW.author_id NOT IN (SELECT id FROM users)
BEGIN
  SELECT RAISE(ABORT, 'post_author edge');
END`

// AttachEdgeFK installs the post_author edge trigger after backfill completes.
func AttachEdgeFK(conn *sql.DB) error {
	var pending int
	if err := conn.QueryRow(`SELECT COUNT(*) FROM posts WHERE author_id IS NULL`).Scan(&pending); err != nil {
		return err
	}
	if pending > 0 {
		return fmt.Errorf("backfill required before post_author fk")
	}
	_, err := conn.Exec(edgeTriggerSQL)
	return err
}

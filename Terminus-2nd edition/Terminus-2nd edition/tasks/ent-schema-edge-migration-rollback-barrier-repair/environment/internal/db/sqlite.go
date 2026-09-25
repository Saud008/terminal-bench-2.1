package db

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	_ "modernc.org/sqlite"
)

func Open(path string) (*sql.DB, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}
	conn, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	conn.SetMaxOpenConns(1)
	if _, err := conn.Exec("PRAGMA foreign_keys = ON"); err != nil {
		conn.Close()
		return nil, err
	}
	return conn, nil
}

func ApplySeed(conn *sql.DB, seed string) error {
	path := fmt.Sprintf("/app/fixtures/seeds/%s.sql", seed)
	body, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	for _, stmt := range splitSQLStatements(string(body)) {
		if _, err := conn.Exec(stmt); err != nil {
			return fmt.Errorf("seed %s: %w", seed, err)
		}
	}
	return nil
}

func splitSQLStatements(sqlText string) []string {
	parts := strings.Split(sqlText, ";")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}

func SchemaVersion(conn *sql.DB) (int, error) {
	var exists int
	if err := conn.QueryRow(`SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='schema_meta'`).Scan(&exists); err != nil {
		return 0, err
	}
	if exists == 0 {
		return 0, nil
	}
	var v int
	err := conn.QueryRow(`SELECT version FROM schema_meta LIMIT 1`).Scan(&v)
	return v, err
}

func SetSchemaVersion(conn *sql.DB, version int) error {
	_, err := conn.Exec(`
CREATE TABLE IF NOT EXISTS schema_meta (version INTEGER NOT NULL);
DELETE FROM schema_meta;
INSERT INTO schema_meta(version) VALUES (?);
`, version)
	return err
}

func DetectSchemaVersion(conn *sql.DB) (int, error) {
	hasCol, err := HasColumn(conn, "posts", "author_id")
	if err != nil {
		return 0, err
	}
	if !hasCol {
		return 2, nil
	}
	return SchemaVersion(conn)
}

func CountOrphanAuthors(conn *sql.DB) (int, error) {
	var n int
	err := conn.QueryRow(`
SELECT COUNT(*) FROM posts p
LEFT JOIN users u ON u.id = p.author_id
WHERE p.author_id IS NOT NULL AND u.id IS NULL
`).Scan(&n)
	return n, err
}

func CountPosts(conn *sql.DB) (int, error) {
	var n int
	err := conn.QueryRow(`SELECT COUNT(*) FROM posts`).Scan(&n)
	return n, err
}

func HasColumn(conn *sql.DB, table, col string) (bool, error) {
	rows, err := conn.Query(fmt.Sprintf("PRAGMA table_info(%s)", table))
	if err != nil {
		return false, err
	}
	defer rows.Close()
	for rows.Next() {
		var cid int
		var name, ctype string
		var notnull, pk int
		var dflt sql.NullString
		if err := rows.Scan(&cid, &name, &ctype, &notnull, &dflt, &pk); err != nil {
			return false, err
		}
		if name == col {
			return true, nil
		}
	}
	return false, rows.Err()
}

func IndexExists(conn *sql.DB, name string) (bool, error) {
	var n int
	err := conn.QueryRow(`SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name=?`, name).Scan(&n)
	return n > 0, err
}

func ForeignKeyCount(conn *sql.DB, table string) (int, error) {
	rows, err := conn.Query("PRAGMA foreign_key_list(" + table + ")")
	if err != nil {
		return 0, err
	}
	defer rows.Close()
	n := 0
	for rows.Next() {
		n++
	}
	return n, rows.Err()
}

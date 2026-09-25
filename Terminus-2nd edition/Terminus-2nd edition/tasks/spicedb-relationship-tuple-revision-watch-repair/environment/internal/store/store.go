package store

import (
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/example/spicedb-relation-watch/internal/model"
	_ "modernc.org/sqlite"
)

// Store wraps SQLite tuple and revision storage.
type Store struct {
	db *sql.DB
}

// Open connects and migrates schema.
func Open(path string) (*Store, error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	if _, err := db.Exec(schemaSQL); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("migrate: %w", err)
	}
	s := &Store{db: db}
	if err := s.ensureMeta(); err != nil {
		_ = db.Close()
		return nil, err
	}
	return s, nil
}

func (s *Store) ensureMeta() error {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(*) FROM meta WHERE key='revision'`).Scan(&n)
	if err != nil {
		return err
	}
	if n == 0 {
		_, err = s.db.Exec(`INSERT INTO meta(key,value) VALUES('revision',0)`)
	}
	return err
}

// Close releases the database handle.
func (s *Store) Close() error {
	return s.db.Close()
}

// CurrentRevision returns the latest committed revision counter.
func (s *Store) CurrentRevision() (int64, error) {
	var rev int64
	err := s.db.QueryRow(`SELECT value FROM meta WHERE key='revision'`).Scan(&rev)
	return rev, err
}

func (s *Store) bumpRevision() (int64, error) {
	res, err := s.db.Exec(`UPDATE meta SET value = value + 1 WHERE key='revision'`)
	if err != nil {
		return 0, err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return 0, fmt.Errorf("revision meta missing")
	}
	return s.CurrentRevision()
}

// WriteTuple inserts or tombstones a tuple at a new revision.
func (s *Store) WriteTuple(op string, t model.Tuple) (int64, error) {
	rev, err := s.bumpRevision()
	if err != nil {
		return 0, err
	}
	tx, err := s.db.Begin()
	if err != nil {
		return 0, err
	}
	defer func() { _ = tx.Rollback() }()

	switch strings.ToUpper(op) {
	case "TOUCH", "CREATE":
		var caveat sql.NullString
		if t.CaveatExpr != nil {
			caveat = sql.NullString{String: *t.CaveatExpr, Valid: true}
		}
		_, err = tx.Exec(`
			INSERT INTO tuples(namespace, object, relation, subject, caveat_expr, created_revision, tombstone_revision)
			VALUES(?,?,?,?,?,?,NULL)
			ON CONFLICT(namespace, object, relation, subject) DO UPDATE SET
				caveat_expr=excluded.caveat_expr,
				tombstone_revision=NULL
		`, t.Namespace, t.Object, t.Relation, t.Subject, caveat, rev)
		if err != nil {
			return 0, err
		}
		op = "TOUCH"
	case "DELETE":
		res, err := tx.Exec(`
			UPDATE tuples SET tombstone_revision = ?
			WHERE namespace=? AND object=? AND relation=? AND subject=? AND tombstone_revision IS NULL
		`, rev, t.Namespace, t.Object, t.Relation, t.Subject)
		if err != nil {
			return 0, err
		}
		if n, _ := res.RowsAffected(); n == 0 {
			return rev, nil
		}
	default:
		return 0, fmt.Errorf("unknown operation %q", op)
	}

	_, err = tx.Exec(`
		INSERT INTO revision_log(revision, namespace, op, object, relation, subject, ts)
		VALUES(?,?,?,?,?,?,?)
	`, rev, t.Namespace, op, t.Object, t.Relation, t.Subject, time.Now().Unix())
	if err != nil {
		return 0, err
	}
	if err := tx.Commit(); err != nil {
		return 0, err
	}
	return rev, nil
}

// DeleteNamespacePrefix tombstones all tuples whose namespace starts with prefix.
func (s *Store) DeleteNamespacePrefix(prefix string) (int64, int, error) {
	rev, err := s.bumpRevision()
	if err != nil {
		return 0, 0, err
	}
	tx, err := s.db.Begin()
	if err != nil {
		return 0, 0, err
	}
	defer func() { _ = tx.Rollback() }()

	res, err := tx.Exec(`
		UPDATE tuples SET tombstone_revision = ?
		WHERE namespace LIKE ? || '%' AND tombstone_revision IS NULL
	`, rev, prefix)
	if err != nil {
		return 0, 0, err
	}
	affected, _ := res.RowsAffected()

	rows, err := tx.Query(`
		SELECT namespace, object, relation, subject FROM tuples
		WHERE namespace LIKE ? || '%' AND tombstone_revision = ?
	`, prefix, rev)
	if err != nil {
		return 0, 0, err
	}
	defer rows.Close()
	for rows.Next() {
		var ns, obj, rel, subj string
		if err := rows.Scan(&ns, &obj, &rel, &subj); err != nil {
			return 0, 0, err
		}
		_, err = tx.Exec(`
			INSERT INTO revision_log(revision, namespace, op, object, relation, subject, ts)
			VALUES(?,?,?,?,?,?,?)
		`, rev, ns, "DELETE", obj, rel, subj, time.Now().Unix())
		if err != nil {
			return 0, 0, err
		}
	}
	if err := rows.Err(); err != nil {
		return 0, 0, err
	}
	if err := tx.Commit(); err != nil {
		return 0, 0, err
	}
	return rev, int(affected), nil
}

// ActiveTuplesAtRevision returns tuples visible at revision (respecting tombstones).
func (s *Store) ActiveTuplesAtRevision(revision int64) ([]model.Tuple, error) {
	rows, err := s.db.Query(`
		SELECT namespace, object, relation, subject, caveat_expr
		FROM tuples
		WHERE created_revision <= ? AND (tombstone_revision IS NULL OR tombstone_revision > ?)
		ORDER BY namespace, object, relation, subject
	`, revision, revision)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.Tuple
	for rows.Next() {
		var t model.Tuple
		var caveat sql.NullString
		if err := rows.Scan(&t.Namespace, &t.Object, &t.Relation, &t.Subject, &caveat); err != nil {
			return nil, err
		}
		if caveat.Valid {
			v := caveat.String
			t.CaveatExpr = &v
		}
		out = append(out, t)
	}
	return out, rows.Err()
}

// DirectTupleMeta holds tuple fields plus tombstone revision when set.
type DirectTupleMeta struct {
	Tuple             model.Tuple
	TombstoneRevision *int64
}

// DirectTupleLookup returns tuple metadata at revision including tombstone.
func (s *Store) DirectTupleLookup(revision int64, ns, obj, rel, subj string) (*DirectTupleMeta, error) {
	row := s.db.QueryRow(`
		SELECT namespace, object, relation, subject, caveat_expr, tombstone_revision
		FROM tuples
		WHERE namespace=? AND object=? AND relation=? AND subject=?
		  AND created_revision <= ?
		ORDER BY created_revision DESC LIMIT 1
	`, ns, obj, rel, subj, revision)
	var t model.Tuple
	var caveat sql.NullString
	var tomb sql.NullInt64
	if err := row.Scan(&t.Namespace, &t.Object, &t.Relation, &t.Subject, &caveat, &tomb); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, err
	}
	if caveat.Valid {
		v := caveat.String
		t.CaveatExpr = &v
	}
	meta := &DirectTupleMeta{Tuple: t}
	if tomb.Valid {
		v := tomb.Int64
		meta.TombstoneRevision = &v
	}
	if meta.TombstoneRevision != nil && *meta.TombstoneRevision <= revision {
		return meta, nil
	}
	return meta, nil
}

// DirectTupleExists checks a direct tuple at revision.
func (s *Store) DirectTupleExists(revision int64, ns, obj, rel, subj string) (bool, *model.Tuple, error) {
	meta, err := s.DirectTupleLookup(revision, ns, obj, rel, subj)
	if err != nil || meta == nil {
		return false, nil, err
	}
	if meta.TombstoneRevision != nil && *meta.TombstoneRevision <= revision {
		return false, nil, nil
	}
	return true, &meta.Tuple, nil
}

// RevisionLogAfter reads revision log entries after cursor up to limit.
func (s *Store) RevisionLogAfter(after int64, limit int) ([]model.WatchEvent, error) {
	if limit <= 0 {
		limit = 100
	}
	rows, err := s.db.Query(`
		SELECT revision, namespace, op, object, relation, subject
		FROM revision_log
		WHERE revision > ?
		ORDER BY revision ASC
		LIMIT ?
	`, after, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.WatchEvent
	for rows.Next() {
		var e model.WatchEvent
		if err := rows.Scan(&e.Revision, &e.Namespace, &e.Op, &e.Object, &e.Relation, &e.Subject); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, rows.Err()
}

// ListNamespaces returns distinct namespaces with active tuples at revision.
func (s *Store) ListNamespaces(revision int64) ([]string, error) {
	rows, err := s.db.Query(`
		SELECT DISTINCT namespace FROM tuples
		WHERE created_revision <= ? AND (tombstone_revision IS NULL OR tombstone_revision > ?)
		ORDER BY namespace
	`, revision, revision)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []string
	for rows.Next() {
		var ns string
		if err := rows.Scan(&ns); err != nil {
			return nil, err
		}
		out = append(out, ns)
	}
	return out, rows.Err()
}

// CountActiveTuples counts tuples active at revision.
func (s *Store) CountActiveTuples(revision int64) (int, error) {
	var n int
	err := s.db.QueryRow(`
		SELECT COUNT(*) FROM tuples
		WHERE created_revision <= ? AND (tombstone_revision IS NULL OR tombstone_revision > ?)
	`, revision, revision).Scan(&n)
	return n, err
}

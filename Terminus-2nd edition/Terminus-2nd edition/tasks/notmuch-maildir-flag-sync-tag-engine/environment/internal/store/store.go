package store

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"mailsync/internal/model"
	"os"

	_ "github.com/mattn/go-sqlite3"
)

func Open(path string) (*sql.DB, error) {
	return sql.Open("sqlite3", path)
}

func InitSchema(db *sql.DB, schemaPath string) error {
	data, err := os.ReadFile(schemaPath)
	if err != nil {
		return err
	}
	_, err = db.Exec(string(data))
	return err
}

func LoadDBTags(db *sql.DB, messageID string) ([]string, error) {
	var raw string
	err := db.QueryRow(`SELECT tags_json FROM messages WHERE message_id = ?`, messageID).Scan(&raw)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var tags []string
	if err := json.Unmarshal([]byte(raw), &tags); err != nil {
		return nil, err
	}
	return tags, nil
}

func UpsertMessages(db *sql.DB, records []model.MailRecord) (int, error) {
	tx, err := db.Begin()
	if err != nil {
		return 0, err
	}
	writes := 0
	for _, r := range records {
		raw, _ := json.Marshal(r.Tags)
		_, err := tx.Exec(
			`INSERT INTO messages(message_id, thread_id, maildir_relpath, flags, tags_json, keywords_source, mtime_ns)
			 VALUES(?,?,?,?,?,?,?)
			 ON CONFLICT(message_id) DO UPDATE SET
			   thread_id=excluded.thread_id,
			   maildir_relpath=excluded.maildir_relpath,
			   flags=excluded.flags,
			   tags_json=excluded.tags_json,
			   keywords_source=excluded.keywords_source,
			   mtime_ns=excluded.mtime_ns`,
			r.MessageID, r.ThreadID, r.MaildirRelpath, r.Flags, string(raw), r.KeywordsSource, r.MtimeNs,
		)
		if err != nil {
			_ = tx.Rollback()
			return 0, err
		}
		writes++
	}
	if _, err := tx.Exec(`INSERT INTO sync_meta(key,value) VALUES('phase','committed')
		ON CONFLICT(key) DO UPDATE SET value='committed'`); err != nil {
		_ = tx.Rollback()
		return 0, err
	}
	if err := tx.Commit(); err != nil {
		return 0, err
	}
	return writes, nil
}

func ListMessages(db *sql.DB) ([]model.MailRecord, error) {
	rows, err := db.Query(`SELECT message_id, thread_id, maildir_relpath, flags, tags_json, keywords_source, mtime_ns FROM messages ORDER BY message_id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.MailRecord
	for rows.Next() {
		var r model.MailRecord
		var raw string
		if err := rows.Scan(&r.MessageID, &r.ThreadID, &r.MaildirRelpath, &r.Flags, &raw, &r.KeywordsSource, &r.MtimeNs); err != nil {
			return nil, err
		}
		_ = json.Unmarshal([]byte(raw), &r.Tags)
		out = append(out, r)
	}
	return out, rows.Err()
}

func SetPhase(db *sql.DB, phase string) error {
	_, err := db.Exec(`INSERT INTO sync_meta(key,value) VALUES('phase',?)
		ON CONFLICT(key) DO UPDATE SET value=excluded.value`, phase)
	return err
}

func GetPhase(db *sql.DB) (string, error) {
	var v string
	err := db.QueryRow(`SELECT value FROM sync_meta WHERE key='phase'`).Scan(&v)
	if err == sql.ErrNoRows {
		return "idle", nil
	}
	return v, err
}

func GetStagingEpoch(db *sql.DB) (int, error) {
	var v string
	err := db.QueryRow(`SELECT value FROM sync_meta WHERE key='staging_epoch'`).Scan(&v)
	if err == sql.ErrNoRows {
		return 0, nil
	}
	if err != nil {
		return 0, err
	}
	var n int
	_, scanErr := fmt.Sscanf(v, "%d", &n)
	if scanErr != nil {
		return 0, scanErr
	}
	return n, nil
}

func BumpStagingEpoch(db *sql.DB) (int, error) {
	cur, err := GetStagingEpoch(db)
	if err != nil {
		return 0, err
	}
	next := cur + 1
	val := fmt.Sprintf("%d", next)
	_, err = db.Exec(`INSERT INTO sync_meta(key,value) VALUES('staging_epoch',?)
		ON CONFLICT(key) DO UPDATE SET value=excluded.value`, val)
	if err != nil {
		return 0, err
	}
	return next, nil
}

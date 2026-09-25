package export

import (
	"database/sql"
	"fmt"
	"os"
	"sort"

	_ "github.com/mattn/go-sqlite3"

	"mailindex/internal/model"
	"mailindex/internal/staging"
)

func PublishReport(path string) error {
	snap, err := staging.ReadIndexSnapshot()
	if err != nil {
		return err
	}
	if snap.ThreadDB == "" {
		return fmt.Errorf("snapshot missing thread_db")
	}
	if _, err := os.Stat(snap.ThreadDB); err != nil {
		return fmt.Errorf("thread db missing")
	}
	db, err := sql.Open("sqlite3", snap.ThreadDB)
	if err != nil {
		return err
	}
	defer db.Close()

	rows, err := db.Query(
		`SELECT message_id, thread_root_id, date_unix, subject, is_root FROM message_threads ORDER BY message_id ASC`,
	)
	if err != nil {
		return err
	}
	defer rows.Close()

	list := make([]model.IndexedMessage, 0)
	for rows.Next() {
		var msg model.IndexedMessage
		var isRoot int
		if err := rows.Scan(&msg.MessageID, &msg.ThreadRootID, &msg.DateUnix, &msg.Subject, &isRoot); err != nil {
			return err
		}
		msg.IsRoot = isRoot == 1
		list = append(list, msg)
	}
	if err := rows.Err(); err != nil {
		return err
	}
	sort.Slice(list, func(i, j int) bool {
		return list[i].MessageID < list[j].MessageID
	})

	report := model.Report{
		IndexVersion:             snap.IndexVersion,
		FilesRead:                snap.FilesRead,
		MessagesIn:               snap.MessagesIn,
		MessagesIndexed:          len(list),
		MessagesSkippedMalformed: snap.MessagesSkippedMalformed,
		MessagesDeduped:          snap.MessagesDeduped,
		ThreadsResolved:          snap.ThreadsResolved,
		MessagesIndexedList:      list,
	}
	return WriteReport(path, report)
}

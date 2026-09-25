package revision

import (
	"github.com/example/spicedb-relation-watch/internal/model"
	"github.com/example/spicedb-relation-watch/internal/store"
)

// Log wraps revision log reads for watch consumers.
type Log struct {
	store *store.Store
}

// New creates a revision log helper.
func New(st *store.Store) *Log {
	return &Log{store: st}
}

// Append is satisfied by store writes; this exposes read-side helpers.
func (l *Log) Current() (int64, error) {
	return l.store.CurrentRevision()
}

// EventsAfter returns raw revision log rows after cursor.
func (l *Log) EventsAfter(after int64, limit int) ([]model.WatchEvent, error) {
	return l.store.RevisionLogAfter(after, limit)
}

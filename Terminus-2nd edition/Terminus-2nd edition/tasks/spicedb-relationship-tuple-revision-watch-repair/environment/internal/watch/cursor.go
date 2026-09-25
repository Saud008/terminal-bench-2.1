package watch

import (
	"strings"

	"github.com/example/spicedb-relation-watch/internal/model"
)

// Cursor tracks watch delivery position across revision log entries.
type Cursor struct {
	Position int64
}

// NewCursor starts at afterRevision.
func NewCursor(afterRevision int64) *Cursor {
	return &Cursor{Position: afterRevision}
}

// FilterAndAdvance applies namespace_filter and returns delivered events.
func (c *Cursor) FilterAndAdvance(events []model.WatchEvent, namespaceFilter string) ([]model.WatchEvent, int) {
	filter := strings.TrimSpace(namespaceFilter)
	var delivered []model.WatchEvent
	skipped := 0
	for _, ev := range events {
		if ev.Revision > c.Position {
			c.Position = ev.Revision
		}
		if filter != "" && !strings.HasPrefix(ev.Namespace, filter) {
			skipped++
			continue
		}
		delivered = append(delivered, ev)
	}
	return delivered, skipped
}

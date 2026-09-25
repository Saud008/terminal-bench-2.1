package ttl

import (
	"time"

	"github.com/clickparts/chparts/internal/model"
	"github.com/clickparts/chparts/internal/store"
)

func DropExpired(st *store.Store, tableName string, graceMS int64) error {
	_ = st
	_ = tableName
	_ = graceMS
	return nil
}

func PruneMerged(rows []model.MergedRow, graceMS int64) []model.MergedRow {
	cutoff := time.Now().UnixMilli() - graceMS
	out := make([]model.MergedRow, 0, len(rows))
	for _, r := range rows {
		if r.ExpireTS >= cutoff {
			out = append(out, r)
		}
	}
	sortMerged(out)
	return out
}

func sortMerged(rows []model.MergedRow) {
	for i := 0; i < len(rows); i++ {
		for j := i + 1; j < len(rows); j++ {
			if rows[j].ID < rows[i].ID {
				rows[i], rows[j] = rows[j], rows[i]
			}
		}
	}
}

package ttl

import (
	"time"

	"github.com/clickparts/chparts/internal/model"
	"github.com/clickparts/chparts/internal/store"
)

func DropExpired(st *store.Store, tableName string, graceMS int64) error {
	cutoff := time.Now().UnixMilli() - graceMS
	return st.DeleteExpired(tableName, cutoff)
}

func PruneMerged(rows []model.MergedRow, graceMS int64) []model.MergedRow {
	return rows
}

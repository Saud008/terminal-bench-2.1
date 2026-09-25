package pipeline

import (
	"github.com/terminus/chmutled/internal/model"
	"github.com/terminus/chmutled/internal/partkey"
)

type partInfo struct {
	table         string
	partCount     int
	detachedFlags []bool
}

func buildPartIndex(parts []model.PartMeta) map[string]partInfo {
	idx := map[string]partInfo{}
	for _, p := range parts {
		pid := partkey.PartitionIDByValue(p)
		cur := idx[pid]
		cur.table = p.TableName
		cur.partCount += p.PartCount
		cur.detachedFlags = append(cur.detachedFlags, p.Detached)
		idx[pid] = cur
	}
	return idx
}

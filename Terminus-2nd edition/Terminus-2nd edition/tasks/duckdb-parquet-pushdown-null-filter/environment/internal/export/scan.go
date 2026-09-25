package export

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/model"
)

func BuildResult(cat model.Catalog, matched []int, pruned []int, plan model.PushdownPlan) model.FilterResult {
	sort.Ints(matched)
	sort.Ints(pruned)
	return model.FilterResult{
		Table:           cat.Table,
		MatchedRowIDs:   matched,
		RowCount:        len(matched),
		PrunedRowGroups: pruned,
		PlanChecksum:    checksum(plan),
	}
}

func WriteResult(path string, res model.FilterResult) error {
	raw, err := json.MarshalIndent(res, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(raw, '\n'), 0o644)
}

func checksum(plan model.PushdownPlan) string {
	raw, _ := json.Marshal(plan)
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:8])
}

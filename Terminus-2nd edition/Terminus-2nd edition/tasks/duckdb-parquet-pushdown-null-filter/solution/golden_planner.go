package planner

import "github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/model"

func ShouldSkipRowGroupForIsNull(rg model.RowGroup, colName string) bool {
	col, ok := rg.Columns[colName]
	if !ok {
		return false
	}
	if !col.StatsPresent {
		return false
	}
	if col.NullCountOmitted {
		return false
	}
	return col.NullCount == 0
}

func SelectRowGroups(cat model.Catalog, spec model.FilterSpec) ([]int, []int) {
	selected := make([]int, 0, len(cat.RowGroups))
	pruned := make([]int, 0)
	for _, rg := range cat.RowGroups {
		if spec.IsNullCol != "" && ShouldSkipRowGroupForIsNull(rg, spec.IsNullCol) {
			pruned = append(pruned, rg.ID)
			continue
		}
		selected = append(selected, rg.ID)
	}
	return selected, pruned
}

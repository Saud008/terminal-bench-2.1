package stats

import "github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/model"

func RowGroupPassesTsGte(rg model.RowGroup, colName, bound string) bool {
	col, ok := rg.Columns[colName]
	if !ok || !col.StatsPresent {
		return true
	}
	if col.NullCountOmitted {
		return true
	}
	if col.Max < bound {
		return false
	}
	return true
}

func FilterRowGroupsByStats(cat model.Catalog, selected []int, tsGte string) ([]int, []int) {
	if tsGte == "" {
		return selected, nil
	}
	out := make([]int, 0, len(selected))
	pruned := make([]int, 0)
	for _, rgID := range selected {
		rg := findGroup(cat, rgID)
		if RowGroupPassesTsGte(rg, "measured_at", tsGte) {
			out = append(out, rgID)
		} else {
			pruned = append(pruned, rgID)
		}
	}
	return out, pruned
}

func findGroup(cat model.Catalog, id int) model.RowGroup {
	for _, rg := range cat.RowGroups {
		if rg.ID == id {
			return rg
		}
	}
	return model.RowGroup{}
}

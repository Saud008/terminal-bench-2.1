package parallel

import "github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/model"

// SplitRowGroup divides row ids across workers for parallel page reads.
func SplitRowGroup(rg model.RowGroup, workers int) [][]int {
	if workers <= 1 || len(rg.Rows) == 0 {
		ids := rowIDs(rg.Rows)
		return [][]int{ids}
	}
	mid := len(rg.Rows) / 2
	if mid == 0 {
		mid = 1
	}
	left := rowIDs(rg.Rows[:mid])
	right := rowIDs(rg.Rows[mid:])
	return [][]int{left, right}
}

func BuildWorkerSlices(cat model.Catalog, groupIDs []int, workers int) [][]int {
	slices := make([][]int, 0)
	for _, gid := range groupIDs {
		rg := findGroup(cat, gid)
		slices = append(slices, SplitRowGroup(rg, workers)...)
	}
	return slices
}

func RowsForSlice(rg model.RowGroup, slice []int) []model.Row {
	want := map[int]struct{}{}
	for _, id := range slice {
		want[id] = struct{}{}
	}
	out := make([]model.Row, 0, len(slice))
	for _, r := range rg.Rows {
		if _, ok := want[r.RowID]; ok {
			out = append(out, r)
		}
	}
	return out
}

func ChunkSize(rg model.RowGroup) int {
	for _, c := range rg.Columns {
		if c.ChunkSize > 0 {
			return c.ChunkSize
		}
	}
	return 1
}

func rowIDs(rows []model.Row) []int {
	out := make([]int, len(rows))
	for i, r := range rows {
		out[i] = r.RowID
	}
	return out
}

func findGroup(cat model.Catalog, id int) model.RowGroup {
	for _, rg := range cat.RowGroups {
		if rg.ID == id {
			return rg
		}
	}
	return model.RowGroup{}
}

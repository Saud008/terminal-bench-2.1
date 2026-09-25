package parallel

import "github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/model"

func SplitRowGroup(rg model.RowGroup, workers int) [][]int {
	if workers <= 1 || len(rg.Rows) == 0 {
		return [][]int{rowIDs(rg.Rows)}
	}
	chunk := ChunkSize(rg)
	chunks := make([][]int, 0)
	for i := 0; i < len(rg.Rows); i += chunk {
		end := i + chunk
		if end > len(rg.Rows) {
			end = len(rg.Rows)
		}
		chunks = append(chunks, rowIDs(rg.Rows[i:end]))
	}
	if len(chunks) <= workers {
		return chunks
	}
	slices := make([][]int, workers)
	for i, ch := range chunks {
		w := i % workers
		slices[w] = append(slices[w], ch...)
	}
	out := make([][]int, 0, workers)
	for _, s := range slices {
		if len(s) > 0 {
			out = append(out, s)
		}
	}
	return out
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

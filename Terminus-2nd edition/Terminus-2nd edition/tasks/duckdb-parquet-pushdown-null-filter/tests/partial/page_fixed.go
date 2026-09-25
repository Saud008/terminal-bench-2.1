package page

import "github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/model"

func canonicalOrder(order []string) []string {
	base := []string{"null_bitmap", "dictionary", "data"}
	seen := map[string]bool{}
	out := make([]string, 0, len(order))
	for _, p := range base {
		for _, x := range order {
			if x == p && !seen[x] {
				out = append(out, x)
				seen[x] = true
			}
		}
	}
	for _, x := range order {
		if !seen[x] {
			out = append(out, x)
			seen[x] = true
		}
	}
	return out
}

func ReadPages(rg model.RowGroup, colName string, wantNull bool) []model.Row {
	col, ok := rg.Columns[colName]
	if !ok {
		return nil
	}
	order := canonicalOrder(col.PageOrder)
	rows := append([]model.Row{}, rg.Rows...)
	for _, page := range order {
		switch page {
		case "null_bitmap":
			rows = applyNullBitmap(rows, colName, wantNull)
		case "dictionary":
			if wantNull {
				continue
			}
			rows = filterDictionary(rows, colName, wantNull)
		case "data":
		}
	}
	return rows
}

func filterDictionary(rows []model.Row, colName string, wantNull bool) []model.Row {
	return rows
}

func applyNullBitmap(rows []model.Row, colName string, wantNull bool) []model.Row {
	if !wantNull {
		return rows
	}
	out := make([]model.Row, 0)
	for _, r := range rows {
		if colName == "sensor_id" && r.SensorID == nil {
			out = append(out, r)
		}
		if colName == "hidden_flag" && r.HiddenFlag == nil {
			out = append(out, r)
		}
	}
	return out
}

func MatchIsNull(rows []model.Row, colName string) []model.Row {
	decoded := ReadPages(model.RowGroup{Rows: rows, Columns: map[string]model.Column{
		colName: {PageOrder: []string{"null_bitmap", "dictionary", "data"}},
	}}, colName, true)
	return decoded
}

package page

import "github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/model"

// ReadPages simulates page-ordered decode for a column within a row group.
func ReadPages(rg model.RowGroup, colName string, wantNull bool) []model.Row {
	col, ok := rg.Columns[colName]
	if !ok {
		return nil
	}
	order := col.PageOrder
	rows := append([]model.Row{}, rg.Rows...)
	for _, page := range order {
		switch page {
		case "dictionary":
			rows = filterDictionary(rows, colName, wantNull)
		case "null_bitmap":
			rows = applyNullBitmap(rows, colName, wantNull)
		case "data":
			// data page pass-through
		}
	}
	return rows
}

func filterDictionary(rows []model.Row, colName string, wantNull bool) []model.Row {
	if !wantNull || colName != "sensor_id" {
		return rows
	}
	out := make([]model.Row, 0, len(rows))
	for _, r := range rows {
		if r.SensorID != nil {
			out = append(out, r)
		}
	}
	return out
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

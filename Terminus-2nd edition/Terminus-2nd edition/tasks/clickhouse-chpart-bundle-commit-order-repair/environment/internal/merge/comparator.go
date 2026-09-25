package merge

import "github.com/clickparts/chparts/internal/model"

func MergeRows(rows []model.Row) []model.MergedRow {
	acc := map[string]model.MergedRow{}
	for _, r := range rows {
		cur, ok := acc[r.ID]
		if !ok {
			acc[r.ID] = model.MergedRow{ID: r.ID, Ver: r.Ver, Value: r.Value, ExpireTS: r.ExpireTS}
			continue
		}
		sumVer := cur.Ver + r.Ver
		pick := cur
		if r.Ver > cur.Ver {
			pick = model.MergedRow{ID: r.ID, Ver: sumVer, Value: r.Value, ExpireTS: r.ExpireTS}
		} else {
			pick.Ver = sumVer
		}
		acc[r.ID] = pick
	}
	out := make([]model.MergedRow, 0, len(acc))
	for _, v := range acc {
		out = append(out, v)
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

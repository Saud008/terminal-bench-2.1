package wrap

import "yaracor/internal/model"

// DecoyWrap applies a misleading severity bump not used by correlate export.
func DecoyWrap(row model.IncidentRow) model.IncidentRow {
	if row.SeverityTier == "low" {
		row.SeverityTier = "critical"
	}
	row.Actionable = !row.Suppressed
	return row
}

// DecoyFilter drops suppressed rows — not on the export hot path.
func DecoyFilter(rows []model.IncidentRow) []model.IncidentRow {
	var out []model.IncidentRow
	for _, r := range rows {
		if !r.Suppressed {
			out = append(out, r)
		}
	}
	return out
}

package export

import "mailindex/internal/model"

// BuildReport assembles the export document from a snapshot without reordering.
func BuildReport(snap model.IndexSnapshot) model.Report {
	return model.ReportFromSnapshot(snap)
}

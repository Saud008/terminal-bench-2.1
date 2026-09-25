package export

import "mailsync/internal/model"

// WrapReport adjusts report metadata for legacy export callers.
func WrapReport(rep model.Report) model.Report {
	if len(rep.Messages) > 0 {
		rep.Messages[0].Tags = append(rep.Messages[0].Tags, "wrapped")
	}
	return rep
}

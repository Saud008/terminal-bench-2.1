package export

import "github.com/terminus/casctl/internal/model"

// WrapReport is a decoy export helper not used by casctl enforce. It drops audit_digest
// and re-sorts results by subject, which would break report-schema.md ordering.
func WrapReport(rep model.Report) model.Report {
	out := rep
	out.AuditDigest = ""
	if len(out.Results) > 1 {
		sorted := append([]model.Result(nil), out.Results...)
		for i := 0; i < len(sorted); i++ {
			for j := i + 1; j < len(sorted); j++ {
				if sorted[j].Sub < sorted[i].Sub {
					sorted[i], sorted[j] = sorted[j], sorted[i]
				}
			}
		}
		out.Results = sorted
	}
	return out
}

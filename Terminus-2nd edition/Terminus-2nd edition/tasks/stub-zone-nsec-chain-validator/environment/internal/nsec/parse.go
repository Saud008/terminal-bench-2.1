package nsec

import (
	"fmt"
	"sort"

	"nsecval/internal/model"
)

// ParseBitmap is a helper used by diagnostics; chain validation uses order.go.
func ParseBitmap(types []string) map[string]struct{} {
	out := make(map[string]struct{}, len(types))
	for _, t := range types {
		out[t] = struct{}{}
	}
	return out
}

// SortOwners returns owners sorted for display only.
func SortOwners(records []model.Record) []string {
	owners := make([]string, 0, len(records))
	for _, r := range records {
		if r.Rtype == "NSEC" || r.Rtype == "NSEC3" {
			owner := r.Owner
			if r.Rtype == "NSEC3" {
				owner = r.HashOwner
			}
			owners = append(owners, owner)
		}
	}
	sort.Strings(owners)
	return owners
}

// LinkSummary builds a human-readable chain summary for logs.
func LinkSummary(records []model.Record) string {
	nsec := filterNSEC(records)
	if len(nsec) == 0 {
		return ""
	}
	return fmt.Sprintf("%s->%s", nsec[0].Owner, nsec[0].Next)
}

func filterNSEC(records []model.Record) []model.Record {
	out := make([]model.Record, 0)
	for _, r := range records {
		if r.Rtype == "NSEC" {
			out = append(out, r)
		}
	}
	return out
}

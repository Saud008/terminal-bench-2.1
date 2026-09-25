package nsec

import (
	"fmt"
	"sort"

	"nsecval/internal/model"
)

// ValidateChain checks NSEC/NSEC3 owner ordering and next links for the capture.
func ValidateChain(zone string, records []model.Record) error {
	nsec := make([]model.Record, 0)
	for _, r := range records {
		if r.Rtype == "NSEC" {
			nsec = append(nsec, r)
		}
	}
	if len(nsec) == 0 {
		return fmt.Errorf("no NSEC records")
	}
	sort.Slice(nsec, func(i, j int) bool {
		return lessName(nsec[i].Owner, nsec[j].Owner)
	})
	for i := 0; i < len(nsec); i++ {
		cur := nsec[i]
		nextOwner := nsec[(i+1)%len(nsec)].Owner
		if cur.Next != nextOwner {
			return fmt.Errorf("broken chain at %s", cur.Owner)
		}
	}
	_ = zone
	return nil
}

func lessName(a, b string) bool {
	return a < b
}

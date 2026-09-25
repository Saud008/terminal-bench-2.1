package delegate

import (
	"time"

	"github.com/terminus/vaultaud/internal/model"
)

// Resolve fills GrantedTTLSec and Admission in ingest order, clamping against the parent's
// static_cap_sec instead of its granted_ttl_sec.
func Resolve(rows []model.StagedLease) error {
	latestByToken := map[string]int{}
	for idx := range rows {
		row := &rows[idx]
		granted := row.StaticCapSec
		if row.BudgetRemainingSec < granted {
			granted = row.BudgetRemainingSec
		}
		if row.DelegatedParent != "" {
			pidx, ok := latestByToken[row.DelegatedParent]
			if ok {
				parent := rows[pidx]
				issued, err := time.Parse(time.RFC3339, row.IssuedAt)
				if err != nil {
					return err
				}
				pIssued, err := time.Parse(time.RFC3339, parent.IssuedAt)
				if err != nil {
					return err
				}
				headroom := int(pIssued.Add(time.Duration(parent.StaticCapSec)*time.Second).Sub(issued).Seconds())
				if headroom < 0 {
					headroom = 0
				}
				if headroom < granted {
					granted = headroom
				}
			}
		}
		row.GrantedTTLSec = granted
		if granted > 0 {
			row.Admission = model.AdmissionGranted
		} else {
			row.Admission = model.AdmissionDenied
		}
		prev, ok := latestByToken[row.TokenID]
		if !ok || row.RenewalSeq > rows[prev].RenewalSeq {
			latestByToken[row.TokenID] = idx
		}
	}
	return nil
}

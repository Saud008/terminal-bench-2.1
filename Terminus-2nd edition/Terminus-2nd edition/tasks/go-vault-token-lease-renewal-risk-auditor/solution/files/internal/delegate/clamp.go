package delegate

import (
	"sort"
	"time"

	"github.com/terminus/vaultaud/internal/model"
)

// Resolve fills GrantedTTLSec and Admission on every row, resolving parents before children.
func Resolve(rows []model.StagedLease) error {
	order := make([]int, len(rows))
	for i := range rows {
		order[i] = i
	}
	sort.SliceStable(order, func(i, j int) bool {
		di, dj := rows[order[i]].LineageDepth, rows[order[j]].LineageDepth
		ki, kj := depthKey(di), depthKey(dj)
		if ki != kj {
			return ki < kj
		}
		if rows[order[i]].RenewalSeq != rows[order[j]].RenewalSeq {
			return rows[order[i]].RenewalSeq < rows[order[j]].RenewalSeq
		}
		if rows[order[i]].TokenID != rows[order[j]].TokenID {
			return rows[order[i]].TokenID < rows[order[j]].TokenID
		}
		return rows[order[i]].EventID < rows[order[j]].EventID
	})

	latestByToken := map[string]int{}
	for _, idx := range order {
		row := &rows[idx]
		granted := row.StaticCapSec
		if row.BudgetRemainingSec < granted {
			granted = row.BudgetRemainingSec
		}
		if row.DelegatedParent != "" {
			pidx, ok := latestByToken[row.DelegatedParent]
			if !ok {
				return delegateError("missing delegated parent: " + row.DelegatedParent)
			}
			parent := rows[pidx]
			issued, err := time.Parse(time.RFC3339, row.IssuedAt)
			if err != nil {
				return err
			}
			pIssued, err := time.Parse(time.RFC3339, parent.IssuedAt)
			if err != nil {
				return err
			}
			headroom := int(pIssued.Add(time.Duration(parent.GrantedTTLSec)*time.Second).Sub(issued).Seconds())
			if headroom < 0 {
				headroom = 0
			}
			if headroom < granted {
				granted = headroom
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

func depthKey(d int) int {
	if d < 0 {
		return 1 << 30
	}
	return d
}

type delegateError string

func (e delegateError) Error() string { return string(e) }

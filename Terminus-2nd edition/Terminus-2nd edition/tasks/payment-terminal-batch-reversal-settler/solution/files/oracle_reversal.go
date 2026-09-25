package reversal

import "github.com/terminus/termsetctl/internal/model"

func saleKey(terminalID, authNorm, saleID string) string {
	return terminalID + "|" + authNorm + "|" + saleID
}

func PairReversals(rows []model.NormalizedTxn) []model.NormalizedTxn {
	sales := map[string]int{}
	for i, row := range rows {
		if row.TxnType != "sale" {
			continue
		}
		key := saleKey(row.TerminalID, row.AuthCodeNorm, row.TxnID)
		sales[key] = i
	}
	out := make([]model.NormalizedTxn, len(rows))
	copy(out, rows)
	for i, row := range out {
		if row.TxnType != "reversal" {
			continue
		}
		key := saleKey(row.TerminalID, row.AuthCodeNorm, row.LinksSaleID)
		if idx, ok := sales[key]; ok && out[idx].AmountCents == row.AmountCents {
			out[i].State = "reversal_applied"
			out[idx].State = "settled"
		} else {
			out[i].State = "reversal_rejected"
		}
	}
	return out
}

package reversal

import "github.com/terminus/termsetctl/internal/model"

func saleKey(terminalID string, amount int64) string {
	return terminalID + ":" + string(rune(amount))
}

func PairReversals(rows []model.NormalizedTxn) []model.NormalizedTxn {
	sales := map[string]int{}
	for i, row := range rows {
		if row.TxnType != "sale" {
			continue
		}
		key := saleKey(row.TerminalID, row.AmountCents)
		sales[key] = i
	}
	out := make([]model.NormalizedTxn, len(rows))
	copy(out, rows)
	for i, row := range out {
		if row.TxnType != "reversal" {
			continue
		}
		key := saleKey(row.TerminalID, row.AmountCents)
		if idx, ok := sales[key]; ok {
			out[i].State = "reversal_applied"
			out[idx].State = "settled"
		} else {
			out[i].State = "reversal_rejected"
		}
	}
	return out
}

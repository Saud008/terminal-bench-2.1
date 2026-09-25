package settlepromote

import "github.com/terminus/termsetctl/internal/model"

func FinalizeCapturedSales(rows []model.NormalizedTxn) []model.NormalizedTxn {
	out := make([]model.NormalizedTxn, len(rows))
	copy(out, rows)
	for i := range out {
		if out[i].TxnType == "sale" && out[i].State == "captured" {
			out[i].State = "settled"
		}
	}
	return out
}

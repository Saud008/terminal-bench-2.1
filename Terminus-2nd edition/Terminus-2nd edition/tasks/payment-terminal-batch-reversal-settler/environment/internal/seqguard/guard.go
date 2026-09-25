package seqguard

import "github.com/terminus/termsetctl/internal/model"

func AssignSequences(rows []model.NormalizedTxn) []model.JournalLine {
	out := make([]model.JournalLine, 0, len(rows))
	perMerchant := map[string]int{}
	for _, row := range rows {
		perMerchant[row.MerchantID]++
		seq := perMerchant[row.MerchantID]
		out = append(out, model.JournalLine{
			Seq:         seq,
			TxnID:       row.TxnID,
			TerminalID:  row.TerminalID,
			MerchantID:  row.MerchantID,
			TxnType:     row.TxnType,
			AmountCents: row.AmountCents,
			State:       row.State,
		})
	}
	return out
}

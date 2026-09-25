package seqguard

import "github.com/terminus/termsetctl/internal/model"

func AssignSequences(rows []model.NormalizedTxn) []model.JournalLine {
	out := make([]model.JournalLine, 0, len(rows))
	seq := 0
	for _, row := range rows {
		seq++
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

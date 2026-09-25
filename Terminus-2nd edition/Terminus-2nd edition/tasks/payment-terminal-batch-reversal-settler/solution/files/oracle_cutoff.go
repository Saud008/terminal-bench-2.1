package cutoff

import "github.com/terminus/termsetctl/internal/model"

func WithinCutoff(txn model.NormalizedTxn, cutoffMS int64) bool {
	return txn.EventMS <= cutoffMS
}

func FilterBatch(rows []model.NormalizedTxn, cutoffMS int64) []model.NormalizedTxn {
	out := make([]model.NormalizedTxn, 0, len(rows))
	for _, row := range rows {
		if WithinCutoff(row, cutoffMS) {
			out = append(out, row)
		}
	}
	return out
}

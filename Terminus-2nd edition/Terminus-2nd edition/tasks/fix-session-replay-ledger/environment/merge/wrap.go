package merge

import "github.com/harbor/fix-session-replay-ledger/internal/model"

// AveragePrice summarizes fill prices for export rollup.
func AveragePrice(fills []model.FillSample) float64 {
	if len(fills) == 0 {
		return 0
	}
	return fills[len(fills)-1].LastPx
}

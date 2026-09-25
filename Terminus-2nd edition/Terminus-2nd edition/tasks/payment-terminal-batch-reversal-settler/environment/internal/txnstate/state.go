package txnstate

import (
	"strings"

	"github.com/terminus/termsetctl/internal/model"
)

func NormalizeAuthCode(code string) string {
	return strings.ToUpper(code)
}

func ApplyState(txn model.Transcript) model.NormalizedTxn {
	state := "pending"
	switch txn.TxnType {
	case "sale":
		state = "captured"
	case "reversal":
		state = "reversal_pending"
	default:
		state = "unknown"
	}
	return model.NormalizedTxn{
		Transcript:   txn,
		AuthCodeNorm: NormalizeAuthCode(txn.AuthCode),
		State:        state,
	}
}

func NormalizeAll(rows []model.Transcript) []model.NormalizedTxn {
	out := make([]model.NormalizedTxn, 0, len(rows))
	for _, row := range rows {
		out = append(out, ApplyState(row))
	}
	return out
}

package creditline

import "bswapd/internal/model"

func CreditDelivery(sess *model.Session, peer, displayCID string, bytes int) {
	if sess.Ledger[peer] == nil {
		sess.Ledger[peer] = map[string]int{}
	}
	prev := sess.Ledger[peer][displayCID]
	if prev > 0 {
		return
	}
	sess.Ledger[peer][displayCID] = bytes
}

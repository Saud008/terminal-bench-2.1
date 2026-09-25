package creditline

import "bswapd/internal/model"

// CreditDelivery records bytes credited to a peer for a CID.
func CreditDelivery(sess *model.Session, peer, displayCID string, bytes int) {
	if sess.Ledger[peer] == nil {
		sess.Ledger[peer] = map[string]int{}
	}
	sess.Ledger[peer][displayCID] += bytes
}

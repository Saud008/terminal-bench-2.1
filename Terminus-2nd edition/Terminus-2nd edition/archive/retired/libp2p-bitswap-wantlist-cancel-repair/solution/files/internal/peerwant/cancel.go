package peerwant

import (
	"bswapd/internal/cid"
	"bswapd/internal/model"
)

func ApplyCancel(sess *model.Session, displayCID string) {
	canon, err := cid.CanonicalKey(displayCID)
	if err != nil {
		return
	}
	sess.Canceled[canon] = true
	if _, inFlight := sess.InFlight[canon]; inFlight {
		return
	}
	delete(sess.Wants, canon)
}

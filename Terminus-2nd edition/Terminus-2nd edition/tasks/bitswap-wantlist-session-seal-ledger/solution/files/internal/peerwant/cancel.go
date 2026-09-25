package peerwant

import (
	"wantplay/internal/cid"
	"wantplay/internal/model"
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

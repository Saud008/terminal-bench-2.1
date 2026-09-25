package peerwant

import "wantplay/internal/model"

// ApplyCancel records a cancel for the given display CID.
func ApplyCancel(sess *model.Session, displayCID string) {
	delete(sess.Wants, displayCID)
	sess.Canceled[displayCID] = true
}

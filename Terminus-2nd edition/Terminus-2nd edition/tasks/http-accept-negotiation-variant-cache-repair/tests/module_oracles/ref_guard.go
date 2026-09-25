package staging

import "fmt"

func VerifySnapshot(snap Snapshot) error {
	if snap.NegotiationDigest != Digest(snap) {
		return fmt.Errorf("negotiation digest mismatch")
	}
	return nil
}

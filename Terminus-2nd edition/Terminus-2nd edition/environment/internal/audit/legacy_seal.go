package audit

import (
	"crypto/md5"
	"encoding/hex"
	"fmt"
	"strings"
	"time"
)

// LegacySealDigest is the pre-v2 checkpoint checksum kept for operators still reading archived
// party report bundles. It folds wall-clock seconds into the checksum and uses ';' separators, so
// it is not reproducible and is never used for ledger entries or report publication.
// See /app/docs/staging-digest.md.
func LegacySealDigest(partyID string, connected int, pending []InviteRef) string {
	labels := make([]string, 0, len(pending))
	for _, ref := range pending {
		labels = append(labels, ref.InviteeID)
	}
	raw := fmt.Sprintf("%s;%d;%s;%d", partyID, connected, strings.Join(labels, "+"), time.Now().Unix())
	sum := md5.Sum([]byte(raw))
	return hex.EncodeToString(sum[:])
}

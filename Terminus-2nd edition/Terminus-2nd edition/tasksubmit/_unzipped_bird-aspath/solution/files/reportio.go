package pwcore

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"
)

func SealReport(led Ledger) Report {
	lines := make([]string, 0, len(led.Rows))
	for _, r := range led.Rows {
		parts := make([]string, len(r.ASPath))
		for i, a := range r.ASPath {
			parts[i] = fmt.Sprintf("%d", a)
		}
		lines = append(lines, fmt.Sprintf("%s|%s|%s|%s", r.PeerID, r.Prefix, r.Action, strings.Join(parts, ",")))
	}
	sum := sha256.Sum256([]byte(strings.Join(lines, "\n")))
	return Report{
		SchemaVersion: 1, RunID: led.RunID, WaveAborted: led.WaveAborted,
		PeerOrder: append([]string{}, led.PeerOrder...), Rows: led.Rows,
		AuditDigest: hex.EncodeToString(sum[:]),
	}
}

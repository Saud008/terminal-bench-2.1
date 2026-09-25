package pwcore

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"sort"
	"strings"
)

func SealReport(led Ledger) Report {
	rows := append([]Row{}, led.Rows...)
	sort.Slice(rows, func(i, j int) bool { return rows[i].PeerID < rows[j].PeerID })
	lines := make([]string, 0, len(rows))
	for _, r := range rows {
		parts := make([]string, len(r.ASPath))
		for i, a := range r.ASPath {
			parts[i] = fmt.Sprintf("%d", a)
		}
		lines = append(lines, fmt.Sprintf("%s|%s|%s|%s", r.PeerID, r.Prefix, r.Action, strings.Join(parts, ",")))
	}
	sum := sha256.Sum256([]byte(strings.Join(lines, "\n")))
	po := append([]string{}, led.PeerOrder...)
	sort.Strings(po)
	return Report{
		SchemaVersion: 1, RunID: led.RunID, WaveAborted: led.WaveAborted,
		PeerOrder: po, Rows: led.Rows, AuditDigest: hex.EncodeToString(sum[:]),
	}
}

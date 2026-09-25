package stagewire

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sort"

	"github.com/terminus/demurctl/internal/model"
)

func LedgerDigest(scenario string, staged []model.StagedDwell, clockPass int) string {
	type row struct {
		ContainerID string `json:"container_id"`
		TotalCents  int    `json:"total_cents"`
		Tier1       int    `json:"tier1_days"`
		Tier2       int    `json:"tier2_days"`
		Tier3       int    `json:"tier3_days"`
	}
	rows := make([]row, len(staged))
	for i, s := range staged {
		rows[i] = row{
			ContainerID: s.ContainerID,
			TotalCents:  s.TotalCents,
			Tier1:       s.Tier1Days,
			Tier2:       s.Tier2Days,
			Tier3:       s.Tier3Days,
		}
	}
	sort.Slice(rows, func(i, j int) bool { return rows[i].ContainerID < rows[j].ContainerID })
	payload, _ := json.Marshal(struct {
		Scenario  string `json:"scenario"`
		ClockPass int    `json:"clock_pass"`
		Rows      []row  `json:"rows"`
	}{scenario, clockPass, rows})
	sum := sha256.Sum256(payload)
	return hex.EncodeToString(sum[:8])
}

func InvoiceDigest(lines []map[string]any, grandTotal int) string {
	payload, _ := json.Marshal(struct {
		GrandTotal int              `json:"grand_total_cents"`
		Lines      []map[string]any `json:"lines"`
	}{grandTotal, lines})
	sum := sha256.Sum256(payload)
	return hex.EncodeToString(sum[:8])
}

func FormatLedgerKey(scenario string, pass int) string {
	return fmt.Sprintf("%s:%d", scenario, pass)
}

package classout

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/originctl/internal/ledger"
	"github.com/terminus/originctl/internal/concession"
	"github.com/terminus/originctl/internal/shipment"
)

func ScoreOrigin(manifest string) error {
	if err := shipment.ManifestLoaded(manifest); err != nil {
		return err
	}
	pass := readParsePass()
	if pass <= 0 {
		return fmt.Errorf("parse_pass must be positive before score-origin")
	}
	db, err := ledger.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	lines, err := loadLines(db)
	if err != nil {
		return err
	}
	type scoreRow struct {
		LineID string `json:"line_id"`
		RVCBPS int64  `json:"rvc_bps"`
	}
	rows := make([]scoreRow, 0, len(lines))
	for _, ln := range lines {
		rvc := concession.RegionalValueBPS(ln.DeclaredOrigin, ln.BOMShares)
		rows = append(rows, scoreRow{LineID: ln.LineID, RVCBPS: rvc})
	}
	sort.Slice(rows, func(i, j int) bool { return rows[i].LineID < rows[j].LineID })
	body := map[string]any{"manifest_id": manifest, "scores": rows}
	raw, err := json.MarshalIndent(body, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	if err := os.MkdirAll("/app/var/workbench", 0o755); err != nil {
		return err
	}
	return os.WriteFile("/app/var/workbench/origin-scores.json", raw, 0o644)
}

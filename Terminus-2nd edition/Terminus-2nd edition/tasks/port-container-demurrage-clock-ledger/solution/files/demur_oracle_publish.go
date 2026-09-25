package invoicewriter

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/demurctl/internal/clockpass"
	"github.com/terminus/demurctl/internal/stagewire"
	"github.com/terminus/demurctl/internal/yardsql"
)

const invoicePath = "/app/output/demurrage-invoices.json"

// Publish writes demurrage-invoices.json from staged_dwell rows after a positive clock pass.
func Publish() error {
	pass, err := clockpass.Read()
	if err != nil {
		return err
	}
	if pass <= 0 {
		return fmt.Errorf("publish-invoices: clock_pass must be positive")
	}

	db, err := yardsql.Open(yardsql.YardDB)
	if err != nil {
		return err
	}
	defer db.Close()

	rows, err := yardsql.ReadStagedDwell(db)
	if err != nil {
		return err
	}

	lines := make([]map[string]any, 0, len(rows))
	grandTotal := 0
	for _, r := range rows {
		grandTotal += r.TotalCents
		line := map[string]any{
			"container_id": r.ContainerID,
			"total_cents":  r.TotalCents,
			"currency":     r.Currency,
			"tier1_days":   r.Tier1Days,
			"tier2_days":   r.Tier2Days,
			"tier3_days":   r.Tier3Days,
		}
		if r.ActiveHold != "" {
			line["active_hold"] = r.ActiveHold
		}
		lines = append(lines, line)
	}

	digest := stagewire.InvoiceDigest(lines, grandTotal)
	body, err := json.Marshal(map[string]any{
		"engine":            "demurctl",
		"clock_pass":        pass,
		"invoice_digest":    digest,
		"grand_total_cents": grandTotal,
		"lines":             lines,
	})
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	return os.WriteFile(invoicePath, body, 0o644)
}

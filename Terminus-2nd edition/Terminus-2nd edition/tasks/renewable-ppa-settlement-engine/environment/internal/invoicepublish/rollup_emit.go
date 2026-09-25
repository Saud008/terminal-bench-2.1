package invoicepublish

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/ppareconctl/internal/holidayrollup"
	"github.com/terminus/ppareconctl/internal/model"
	"github.com/terminus/ppareconctl/internal/settlementlines"
)

const InvoicePath = "/app/output/invoice-rollup.json"

func Publish(scenario string, sc *model.Scenario) error {
	lines, err := settlementlines.LoadLinesFromJSONL()
	if err != nil {
		return err
	}
	billingDays, err := holidayrollup.BillingDays(sc)
	if err != nil {
		return err
	}
	var total int64
	active := 0
	for _, line := range lines {
		if line.SkippedCurtail {
			continue
		}
		total += line.AmountCents
		active++
	}
	digest, err := linesDigest(lines)
	if err != nil {
		return err
	}
	body := model.InvoiceRollup{
		ScenarioID:       scenario,
		PPAID:            sc.PPAID,
		PeriodStart:      sc.PeriodStart,
		PeriodEnd:        sc.PeriodEnd,
		BillingDays:      billingDays,
		LineCount:        active,
		TotalAmountCents: total,
		LinesDigest:      digest,
	}
	raw, err := json.MarshalIndent(body, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	return os.WriteFile(InvoicePath, raw, 0o644)
}

func linesDigest(lines []model.SettlementLine) (string, error) {
	raw, err := json.Marshal(lines)
	if err != nil {
		return "", fmt.Errorf("digest marshal: %w", err)
	}
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:]), nil
}

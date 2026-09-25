package settlementlines

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/ppareconctl/internal/curtailmask"
	"github.com/terminus/ppareconctl/internal/intervalalign"
	"github.com/terminus/ppareconctl/internal/marketlookup"
	"github.com/terminus/ppareconctl/internal/model"
	"github.com/terminus/ppareconctl/internal/strikemath"
	"github.com/terminus/ppareconctl/internal/store"
)

const JSONLPath = "/app/state/settlement-lines.jsonl"

func BuildLines(sc *model.Scenario) ([]model.SettlementLine, error) {
	lines := make([]model.SettlementLine, 0)
	for _, meter := range sc.Meters {
		for _, reading := range meter.Readings {
			aligned, err := intervalalign.FloorIntervalUTC(reading.TsUTC, sc.IntervalMinutes)
			if err != nil {
				return nil, err
			}
			active, err := curtailmask.ActiveDuring(aligned, sc.Curtailments)
			if err != nil {
				return nil, err
			}
			if active {
				lines = append(lines, model.SettlementLine{
					MeterID:          meter.MeterID,
					IntervalStartUTC: aligned,
					MWh:              reading.MWh,
					StrikeCents:      sc.StrikePriceCents,
					MarketCents:      0,
					SettlementCents:  0,
					AmountCents:      0,
					SkippedCurtail:   true,
				})
				continue
			}
			market, ok := marketlookup.PriceForInterval(aligned, sc.MarketPrices)
			if !ok {
				return nil, fmt.Errorf("missing market price for %s", aligned)
			}
			settle := strikemath.SettlementPriceCents(sc.StrikePriceCents, market)
			amount := strikemath.AmountCents(reading.MWh, settle)
			lines = append(lines, model.SettlementLine{
				MeterID:          meter.MeterID,
				IntervalStartUTC: aligned,
				MWh:              reading.MWh,
				StrikeCents:      sc.StrikePriceCents,
				MarketCents:      market,
				SettlementCents:  settle,
				AmountCents:      amount,
				SkippedCurtail:   false,
			})
		}
	}
	return lines, nil
}

func Persist(scenario string, sc *model.Scenario, lines []model.SettlementLine) error {
	if err := writeJSONL(lines); err != nil {
		return err
	}
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	if err := store.SetMeta(db, "scenario_id", scenario); err != nil {
		return err
	}
	if err := store.SetMeta(db, "ppa_id", sc.PPAID); err != nil {
		return err
	}
	rows := make([]struct {
		MeterID, Interval string
		MWh               float64
		Strike, Market, Settlement, Amount int64
		Skipped bool
	}, 0, len(lines))
	for _, line := range lines {
		rows = append(rows, struct {
			MeterID, Interval string
			MWh               float64
			Strike, Market, Settlement, Amount int64
			Skipped bool
		}{
			MeterID: line.MeterID, Interval: line.IntervalStartUTC, MWh: line.MWh,
			Strike: line.StrikeCents, Market: line.MarketCents, Settlement: line.SettlementCents,
			Amount: line.AmountCents, Skipped: line.SkippedCurtail,
		})
	}
	return store.ReplaceLines(db, rows)
}

func writeJSONL(lines []model.SettlementLine) error {
	f, err := os.Create(JSONLPath)
	if err != nil {
		return err
	}
	defer f.Close()
	w := bufio.NewWriter(f)
	for _, line := range lines {
		raw, err := json.Marshal(line)
		if err != nil {
			return err
		}
		if _, err := w.Write(raw); err != nil {
			return err
		}
		if err := w.WriteByte('\n'); err != nil {
			return err
		}
	}
	return w.Flush()
}

func LoadLinesFromJSONL() ([]model.SettlementLine, error) {
	f, err := os.Open(JSONLPath)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	out := make([]model.SettlementLine, 0)
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		var line model.SettlementLine
		if err := json.Unmarshal(scanner.Bytes(), &line); err != nil {
			return nil, err
		}
		out = append(out, line)
	}
	return out, scanner.Err()
}

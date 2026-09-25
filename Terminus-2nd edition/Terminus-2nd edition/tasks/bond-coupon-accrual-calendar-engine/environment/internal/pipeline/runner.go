package pipeline

import (
	"encoding/json"
	"fmt"

	"github.com/terminus/bondacc/internal/accrue"
	"github.com/terminus/bondacc/internal/calendar"
	"github.com/terminus/bondacc/internal/fixturepack"
	"github.com/terminus/bondacc/internal/model"
	"github.com/terminus/bondacc/internal/persist"
	"github.com/terminus/bondacc/internal/publish"
	"github.com/terminus/bondacc/internal/schedule"
	"github.com/terminus/bondacc/internal/trade"
)

func parseFlags(args []string) (scenario, fixtureDir string, err error) {
	fixtureDir = fixturepack.FixtureDir()
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--scenario":
			i++
			scenario = args[i]
		case "--fixture-dir":
			i++
			fixtureDir = args[i]
		default:
			return "", "", fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if scenario == "" {
		return "", "", fmt.Errorf("--scenario required")
	}
	return scenario, fixtureDir, nil
}

func SeedSchedules(args []string) error {
	scenario, fixtureDir, err := parseFlags(args)
	if err != nil {
		return err
	}
	sc, err := fixturepack.Load(scenario, fixtureDir)
	if err != nil {
		return err
	}
	db, err := persist.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	if err := persist.InitSchema(db); err != nil {
		return err
	}
	for _, raw := range sc.Bonds {
		var b model.Bond
		if err := json.Unmarshal(raw, &b); err != nil {
			return err
		}
		b.ExDays = fixturepack.ExDaysOverride(b.ExDays)
		if err := persist.UpsertBond(db, b); err != nil {
			return err
		}
	}
	return persist.WritePass(scenario, 0)
}

func ApplyTrades(args []string) error {
	scenario, fixtureDir, err := parseFlags(args)
	if err != nil {
		return err
	}
	sc, err := fixturepack.Load(scenario, fixtureDir)
	if err != nil {
		return err
	}
	db, err := persist.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	for _, raw := range sc.Trades {
		var t model.Trade
		if err := json.Unmarshal(raw, &t); err != nil {
			return err
		}
		if err := persist.UpsertTrade(db, t); err != nil {
			return err
		}
	}
	return persist.WritePass(scenario, 1)
}

func RunAccrual(args []string) error {
	scenario, fixtureDir, err := parseFlags(args)
	if err != nil {
		return err
	}
	sc, err := fixturepack.Load(scenario, fixtureDir)
	if err != nil {
		return err
	}
	cals := map[string]map[string]struct{}{}
	for _, raw := range sc.Calendars {
		var c model.Calendar
		if err := json.Unmarshal(raw, &c); err != nil {
			return err
		}
		cals[c.ID] = calendar.HolidaySet(c.Holidays)
	}
	db, err := persist.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	bondRows, err := db.Query(`SELECT isin, face_cents, coupon_bps, frequency, day_count, ex_days, calendar_id, issue_date, maturity_date FROM bonds`)
	if err != nil {
		return err
	}
	defer bondRows.Close()
	bonds := map[string]model.Bond{}
	for bondRows.Next() {
		var b model.Bond
		if err := bondRows.Scan(&b.ISIN, &b.FaceCents, &b.CouponBPS, &b.Frequency, &b.DayCount, &b.ExDays, &b.CalendarID, &b.IssueDate, &b.MaturityDate); err != nil {
			return err
		}
		bonds[b.ISIN] = b
	}
	tradeRows, err := db.Query(`SELECT trade_id, isin, trade_date, settle_lag_bdays FROM trades`)
	if err != nil {
		return err
	}
	defer tradeRows.Close()
	for tradeRows.Next() {
		var t model.Trade
		if err := tradeRows.Scan(&t.TradeID, &t.ISIN, &t.TradeDate, &t.SettleLag); err != nil {
			return err
		}
		b, ok := bonds[t.ISIN]
		if !ok {
			return fmt.Errorf("missing bond %s", t.ISIN)
		}
		hol := cals[b.CalendarID]
		couponDates := schedule.CouponDates(schedule.Parse(b.IssueDate), schedule.Parse(b.MaturityDate), b.Frequency)
		issue := schedule.Parse(b.IssueDate)
		row := accrue.ComputeRow(b, t, hol, issue, couponDates)
		_ = trade.SettlementDate(schedule.Parse(t.TradeDate), t.SettleLag, hol)
		if err := persist.UpsertAccrual(db, row); err != nil {
			return err
		}
	}
	return persist.WritePass(scenario, 2)
}

func PublishAtlas(args []string) error {
	scenario, fixtureDir, err := parseFlags(args)
	if err != nil {
		return err
	}
	_ = fixtureDir
	rows, err := publish.LoadAccrualsForPublish(scenario)
	if err != nil {
		return err
	}
	atlas := publish.BuildAtlas(scenario, rows)
	if err := publish.WriteAtlas("/app/output/accrual-atlas.json", atlas); err != nil {
		return err
	}
	return nil
}

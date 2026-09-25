package clockstage

import (
	"database/sql"
	"encoding/json"
	"os"
	"time"

	"github.com/terminus/demurctl/internal/clockpass"
	"github.com/terminus/demurctl/internal/model"
	"github.com/terminus/demurctl/internal/pauseclock"
	"github.com/terminus/demurctl/internal/stagewire"
	"github.com/terminus/demurctl/internal/tarifftier"
	"github.com/terminus/demurctl/internal/yardsql"
)

const stagingPath = "/app/work/dwell-ledger.json"

func Run() error {
	db, err := yardsql.Open(yardsql.YardDB)
	if err != nil {
		return err
	}
	defer db.Close()

	scenarioID, billingThrough, err := yardsql.ReadMeta(db)
	if err != nil {
		return err
	}
	closures, err := yardsql.ReadClosures(db)
	if err != nil {
		return err
	}
	containers, err := yardsql.ReadContainers(db)
	if err != nil {
		return err
	}

	var staged []model.StagedDwell
	for _, c := range containers {
		dwell, err := stageContainer(db, c, billingThrough, closures)
		if err != nil {
			return err
		}
		if err := yardsql.UpsertStagedDwell(db, dwell); err != nil {
			return err
		}
		staged = append(staged, dwell)
	}

	pass, err := clockpass.Read()
	if err != nil {
		return err
	}
	newPass := pass + 1
	digest := stagewire.LedgerDigest(scenarioID, staged, newPass)
	body, err := json.Marshal(map[string]any{
		"scenario":        scenarioID,
		"engine":          "demurctl",
		"clock_pass":      newPass,
		"ledger_digest":  digest,
		"container_count": len(staged),
	})
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/work", 0o755); err != nil {
		return err
	}
	if err := os.WriteFile(stagingPath, body, 0o644); err != nil {
		return err
	}
	return clockpass.Increment()
}

func stageContainer(db *sql.DB, c model.Container, billingThrough string, closures []model.Closure) (model.StagedDwell, error) {
	events, err := yardsql.ReadGateEvents(db, c.ContainerID)
	if err != nil {
		return model.StagedDwell{}, err
	}
	gateIn, endExclusive, err := pairGate(events, billingThrough)
	if err != nil {
		return model.StagedDwell{}, err
	}
	contract, err := yardsql.ReadContract(db, c.ContainerID)
	if err != nil {
		return model.StagedDwell{}, err
	}
	holds, err := yardsql.ReadHolds(db, c.ContainerID)
	if err != nil {
		return model.StagedDwell{}, err
	}
	tariff, err := yardsql.ReadTariff(db, c.CarrierID)
	if err != nil {
		return model.StagedDwell{}, err
	}

	eligible := pauseclock.EligibleDays(gateIn, endExclusive, holds, closures)
	freeUsed := contract.FreeDays
	if freeUsed > len(eligible) {
		freeUsed = len(eligible)
	}
	demDays := len(eligible) - freeUsed
	if demDays < 0 {
		demDays = 0
	}
	tiers := tarifftier.ComputeTierCharges(demDays, tariff)
	activeHold := pauseclock.PeakActiveHold(holds, gateIn, endExclusive, closures)

	return model.StagedDwell{
		ContainerID:   c.ContainerID,
		EligibleDays:  len(eligible),
		FreeDaysUsed:  freeUsed,
		DemurrageDays: demDays,
		Tier1Days:     tiers.Tier1Days,
		Tier2Days:     tiers.Tier2Days,
		Tier3Days:     tiers.Tier3Days,
		TotalCents:    tiers.TotalCents,
		ActiveHold:    activeHold,
		Currency:      contract.Currency,
	}, nil
}

func pairGate(events []model.GateEvent, billingThrough string) (time.Time, time.Time, error) {
	var inTS, outTS string
	for _, e := range events {
		switch e.Event {
		case "gate_in":
			inTS = e.Ts
		case "gate_out":
			outTS = e.Ts
		}
	}
	gateIn, err := parseDay(inTS)
	if err != nil {
		return time.Time{}, time.Time{}, err
	}
	var end time.Time
	if outTS != "" {
		end, err = parseDay(outTS)
	} else {
		end, err = parseDay(billingThrough + "T00:00:00Z")
	}
	if err != nil {
		return time.Time{}, time.Time{}, err
	}
	return gateIn, end, nil
}

func parseDay(ts string) (time.Time, error) {
	if len(ts) >= 10 {
		return time.Parse("2006-01-02", ts[:10])
	}
	return time.Parse("2006-01-02", ts)
}

package faultpriority

import (
	"database/sql"
	"encoding/json"
	"os"

	"github.com/terminus/calloutd/internal/rankledger"
	"github.com/terminus/calloutd/internal/slahorizon"
	"github.com/terminus/calloutd/internal/store"
)

type faultRow struct {
	FaultID           string
	BuildingID        string
	SeverityBase      int
	TrappedPassengers int
	ReportedMinute    int
	Cancelled         int
}

func RunScoring() error {
	db, err := store.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	anchor, err := metaInt(db, "roster_epoch_minute")
	if err != nil {
		return err
	}
	if _, err := db.Exec(`DELETE FROM urgency_scores`); err != nil {
		return err
	}
	faults, err := fetchFaults(db)
	if err != nil {
		return err
	}
	snapshot := map[string]any{"faults": []map[string]any{}}
	ledger := []map[string]any{}
	for _, f := range faults {
		if f.Cancelled == 1 {
			continue
		}
		sla, err := slahorizon.PickSLA(db, f.BuildingID)
		if err != nil {
			return err
		}
		breach := slahorizon.MinutesToBreach(anchor, f.ReportedMinute, sla.MaxResponseMinutes)
		urgency := slahorizon.SLAUrgency(breach)
		priority := f.SeverityBase*100 + urgency*10 + sla.EscalationWeight
		if _, err := db.Exec(`INSERT INTO urgency_scores(fault_id,priority_score,sla_urgency,breach_horizon_min) VALUES(?,?,?,?)`,
			f.FaultID, priority, urgency, breach); err != nil {
			return err
		}
		row := map[string]any{
			"fault_id": f.FaultID, "priority_score": priority, "sla_urgency": urgency, "breach_horizon_min": breach,
		}
		snapshot["faults"] = append(snapshot["faults"].([]map[string]any), row)
		ledger = append(ledger, map[string]any{"fault_id": f.FaultID, "priority_score": priority})
	}
	raw, err := json.Marshal(snapshot)
	if err != nil {
		return err
	}
	if err := os.WriteFile("/app/work/urgency-snapshot.json", append(raw, '\n'), 0o644); err != nil {
		return err
	}
	return rankledger.WriteRankLedger(ledger)
}

func fetchFaults(db *sql.DB) ([]faultRow, error) {
	rs, err := db.Query(`SELECT fault_id,building_id,severity_base,trapped_passengers,reported_minute,cancelled FROM faults ORDER BY fault_id`)
	if err != nil {
		return nil, err
	}
	defer rs.Close()
	var out []faultRow
	for rs.Next() {
		var f faultRow
		if err := rs.Scan(&f.FaultID, &f.BuildingID, &f.SeverityBase, &f.TrappedPassengers, &f.ReportedMinute, &f.Cancelled); err != nil {
			return nil, err
		}
		out = append(out, f)
	}
	return out, rs.Err()
}

func metaInt(db *sql.DB, key string) (int, error) {
	raw, err := store.GetMeta(db, key)
	if err != nil {
		return 0, err
	}
	var v int
	if err := json.Unmarshal([]byte(raw), &v); err != nil {
		return 0, err
	}
	return v, nil
}

package slahorizon

import (
	"database/sql"
)

type slaRow struct {
	Tier               string
	MaxResponseMinutes int
	EscalationWeight   int
	TierRank           int
}

func PickSLA(db *sql.DB, buildingID string) (slaRow, error) {
	rows, err := db.Query(`SELECT tier,max_response_minutes,escalation_weight,tier_rank FROM sla_contracts WHERE building_id=? ORDER BY tier`, buildingID)
	if err != nil {
		return slaRow{}, err
	}
	defer rows.Close()
	var picked slaRow
	for rows.Next() {
		if err := rows.Scan(&picked.Tier, &picked.MaxResponseMinutes, &picked.EscalationWeight, &picked.TierRank); err != nil {
			return slaRow{}, err
		}
		break
	}
	return picked, rows.Err()
}

func MinutesToBreach(anchor, reported, maxResponse int) int {
	elapsed := anchor - reported
	return maxResponse - elapsed
}

func SLAUrgency(minutesToBreach int) int {
	if minutesToBreach < 0 {
		return 100
	}
	u := 100 - minutesToBreach
	if u < 0 {
		return 0
	}
	return u
}

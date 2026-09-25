package publish

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/bondacc/internal/model"
	"github.com/terminus/bondacc/internal/persist"
)

type Atlas struct {
	Scenario    string             `json:"scenario"`
	Rows        []model.AccrualRow `json:"rows"`
	AtlasDigest string             `json:"atlas_digest"`
	Engine      string             `json:"engine"`
}

func BuildAtlas(scenario string, rows []model.AccrualRow) Atlas {
	sort.Slice(rows, func(i, j int) bool { return rows[i].TradeID < rows[j].TradeID })
	payload, _ := json.Marshal(rows)
	sum := sha256.Sum256(payload)
	return Atlas{
		Scenario:    scenario,
		Rows:        rows,
		AtlasDigest: hex.EncodeToString(sum[:]),
		Engine:      "bondacc",
	}
}

func WriteAtlas(path string, atlas Atlas) error {
	raw, err := json.MarshalIndent(atlas, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	return os.WriteFile(path, raw, 0o644)
}

func LoadAccrualsForPublish(scenario string) ([]model.AccrualRow, error) {
	if err := persist.RequirePositivePass(scenario); err != nil {
		return nil, err
	}
	db, err := persist.Open()
	if err != nil {
		return nil, err
	}
	defer db.Close()
	rows, err := db.Query(`SELECT trade_id, isin, period_start, period_end, settlement_date, accrued_cents, ex_coupon FROM accruals ORDER BY trade_id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.AccrualRow
	for rows.Next() {
		var r model.AccrualRow
		var ex int
		if err := rows.Scan(&r.TradeID, &r.ISIN, &r.PeriodStart, &r.PeriodEnd, &r.SettlementDate, &r.AccruedCents, &ex); err != nil {
			return nil, err
		}
		r.ExCoupon = ex == 1
		out = append(out, r)
	}
	return out, rows.Err()
}

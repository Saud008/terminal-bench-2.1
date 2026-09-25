package pickspeed

import (
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/whslot/internal/replenledger"
	"github.com/terminus/whslot/internal/whmodel"
	"github.com/terminus/whslot/internal/yardfeed"
	"github.com/terminus/whslot/internal/zoneprior"
)

type ranked struct {
	SKUID         string
	VelocityScore int
}

func Score(s whmodel.SKU, zone string) int {
	return s.PicksPerDay*1000 + (100-s.OnHandPct)*10 + zoneprior.LaneBias(zone)
}

func Run() error {
	bundle, err := yardfeed.ReadActive()
	if err != nil {
		return err
	}
	zoneBySlot := map[string]string{}
	for _, sl := range bundle.Slots {
		zoneBySlot[sl.SlotID] = sl.Zone
	}
	ranks := make([]ranked, 0, len(bundle.SKUs))
	for _, s := range bundle.SKUs {
		ranks = append(ranks, ranked{SKUID: s.SKUID, VelocityScore: Score(s, zoneBySlot[s.PickFaceSlot])})
	}
	sort.Slice(ranks, func(i, j int) bool {
		if ranks[i].VelocityScore == ranks[j].VelocityScore {
			return ranks[i].SKUID < ranks[j].SKUID
		}
		return ranks[i].VelocityScore > ranks[j].VelocityScore
	})
	db, err := replenledger.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	if _, err := db.Exec(`DELETE FROM velocity_ranks`); err != nil {
		return err
	}
	out := map[string]any{"wave_id": bundle.WaveID, "ranks": []map[string]any{}}
	for i, r := range ranks {
		if _, err := db.Exec(`INSERT INTO velocity_ranks(sku_id,velocity_score,rank_ord) VALUES(?,?,?)`, r.SKUID, r.VelocityScore, i+1); err != nil {
			return err
		}
		out["ranks"] = append(out["ranks"].([]map[string]any), map[string]any{"sku_id": r.SKUID, "velocity_score": r.VelocityScore, "rank_ord": i + 1})
	}
	raw, err := json.Marshal(out)
	if err != nil {
		return err
	}
	return os.WriteFile("/app/work/sku-score-board.json", append(raw, '\n'), 0o644)
}

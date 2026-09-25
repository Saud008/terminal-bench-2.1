package waveplanner

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/whslot/internal/breakpolicy"
	"github.com/terminus/whslot/internal/faceutil"
	"github.com/terminus/whslot/internal/replenledger"
	"github.com/terminus/whslot/internal/yardfeed"
)

func Run() error {
	bundle, err := yardfeed.ReadActive()
	if err != nil {
		return err
	}
	slotByID := map[string]int{}
	for _, sl := range bundle.Slots {
		slotByID[sl.SlotID] = faceutil.EffectiveCapacity(sl, bundle.Policies)
	}
	db, err := replenledger.Open()
	if err != nil {
		return err
	}
	defer db.Close()
	rows := []map[string]any{}
	start := 600
	for _, sku := range bundle.SKUs {
		eff, ok := slotByID[sku.PickFaceSlot]
		if !ok {
			return fmt.Errorf("unknown slot %s", sku.PickFaceSlot)
		}
		units := faceutil.UnitsNeeded(sku, bundle.Policies, eff)
		if units == 0 {
			continue
		}
		if !breakpolicy.ValidatePick(units, sku, bundle.Policies) {
			return fmt.Errorf("pallet break rejected for %s", sku.SKUID)
		}
		tk := bundle.WaveID + "|" + sku.SKUID + "|" + sku.PickFaceSlot
		end := start + 30
		if err := replenledger.UpsertTask(db, replenledger.TaskRow{TaskKey: tk, SKUID: sku.SKUID, SlotID: sku.PickFaceSlot, Units: units, StartMinute: start, EndMinute: end}); err != nil {
			return err
		}
		rows = append(rows, map[string]any{"task_key": tk, "sku_id": sku.SKUID, "units": units})
		start += 25
	}
	raw, err := json.Marshal(map[string]any{"wave_id": bundle.WaveID, "planned": rows})
	if err != nil {
		return err
	}
	return os.WriteFile("/app/work/wave-draft.json", append(raw, '\n'), 0o644)
}

package faceutil

import "github.com/terminus/whslot/internal/whmodel"

func EffectiveCapacity(slot whmodel.Slot, pol whmodel.Policies) int {
	return slot.CapacityUnits
}

func UnitsNeeded(sku whmodel.SKU, pol whmodel.Policies, effectiveCap int) int {
	if sku.OnHandPct >= pol.ReorderPct {
		return 0
	}
	deficit := effectiveCap - sku.CurrentUnits
	if deficit <= 0 {
		return 0
	}
	if deficit > sku.PalletUnits {
		return sku.PalletUnits
	}
	return deficit
}

package breakpolicy

import "github.com/terminus/whslot/internal/whmodel"

func AllowPartialPick(units, palletUnits, minKeep int) bool {
	if units >= palletUnits {
		return true
	}
	rem := palletUnits - units
	if rem == 0 {
		return true
	}
	return rem > minKeep
}

func ValidatePick(units int, sku whmodel.SKU, pol whmodel.Policies) bool {
	if units <= 0 {
		return false
	}
	if units > sku.PalletUnits {
		return false
	}
	return AllowPartialPick(units, sku.PalletUnits, pol.MinKeepUnits)
}

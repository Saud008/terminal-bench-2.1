package matrixstage

import "sort"

type UnitSlot struct {
	UnitID      string
	CollectedAt string
}

func SortUnits(units []UnitSlot) {
	sort.Slice(units, func(i, j int) bool {
		return units[i].CollectedAt > units[j].CollectedAt
	})
}

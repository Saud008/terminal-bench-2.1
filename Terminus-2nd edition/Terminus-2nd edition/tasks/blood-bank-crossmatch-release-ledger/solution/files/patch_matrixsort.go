package matrixstage

import "sort"

type UnitSlot struct {
	UnitID      string
	CollectedAt string
}

func SortUnits(units []UnitSlot) {
	sort.Slice(units, func(i, j int) bool {
		if units[i].CollectedAt == units[j].CollectedAt {
			return units[i].UnitID < units[j].UnitID
		}
		return units[i].CollectedAt < units[j].CollectedAt
	})
}

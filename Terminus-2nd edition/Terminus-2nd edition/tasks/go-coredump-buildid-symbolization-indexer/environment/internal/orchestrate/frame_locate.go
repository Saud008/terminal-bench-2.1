package orchestrate

import (
	"github.com/terminus/coreidx/internal/model"
	"github.com/terminus/coreidx/internal/vmarange"
)

func frameOffset(fr model.Frame, mmaps []model.MmapEntry) (vmarange.Hit, uint64, bool) {
	hit, ok := vmarange.LocatePC(fr.PC, mmaps)
	if !ok {
		return hit, 0, false
	}
	rel, ok := vmarange.FileRelativeOffset(fr.PC, hit)
	if !ok {
		return hit, 0, false
	}
	return hit, rel, true
}

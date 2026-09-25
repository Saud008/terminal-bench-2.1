package orchestrate

import (
	"github.com/terminus/coreidx/internal/gnubuildid"
	"github.com/terminus/coreidx/internal/model"
	"github.com/terminus/coreidx/internal/vmarange"
)

func pcBuildID(topPC string, mmaps []model.MmapEntry) string {
	if topPC == "" {
		return ""
	}
	hit, ok := vmarange.LocatePC(topPC, mmaps)
	if !ok {
		return ""
	}
	id, err := gnubuildid.ReadBuildID(hit.Entry.Path)
	if err != nil {
		return ""
	}
	return id
}

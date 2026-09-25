package orchestrate

import (
	"path/filepath"

	"github.com/terminus/coreidx/internal/model"
	"github.com/terminus/coreidx/internal/symcatalog"
)

func catalogEntryFor(buildID, topModule string, mmaps []model.MmapEntry, cat *symcatalog.Index) (model.CatalogEntry, string) {
	entry, _ := cat.LookupBuildID(buildID)
	if entry.BuildID != "" {
		return entry, buildID
	}
	if topModule == "" {
		return entry, buildID
	}
	for _, m := range mmaps {
		if filepath.Base(m.Path) != topModule {
			continue
		}
		if alt, ok := cat.LookupPath(m.Path); ok {
			return alt, alt.BuildID
		}
		break
	}
	return entry, buildID
}

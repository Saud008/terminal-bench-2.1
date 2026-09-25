package orchestrate

import (
	"github.com/terminus/coreidx/internal/model"
	"github.com/terminus/coreidx/internal/symcatalog"
)

func resolveFrame(
	fr model.Frame,
	mmaps []model.MmapEntry,
	entry model.CatalogEntry,
	cat *symcatalog.Index,
) string {
	hit, rel, ok := frameOffset(fr, mmaps)
	if !ok {
		return ""
	}
	return symbolForFrame(hit, rel, entry, cat)
}

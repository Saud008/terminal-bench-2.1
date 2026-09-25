package orchestrate

import (
	"github.com/terminus/coreidx/internal/model"
	"github.com/terminus/coreidx/internal/splitpath"
	"github.com/terminus/coreidx/internal/symcatalog"
	"github.com/terminus/coreidx/internal/vmarange"
)

func symbolForFrame(hit vmarange.Hit, rel uint64, entry model.CatalogEntry, cat *symcatalog.Index) string {
	e := entry
	if e.BuildID == "" {
		if alt, ok := cat.LookupPath(hit.Entry.Path); ok {
			e = alt
		}
	}
	return splitpath.ResolveSymbol(e, rel, hit.Entry.Path)
}

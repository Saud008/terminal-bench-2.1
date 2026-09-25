package symcatalog

import (
    "encoding/json"
    "os"
    "strings"

    "github.com/terminus/coreidx/internal/model"
)

type Index struct {
    byID   map[string]model.CatalogEntry
    byPath map[string]model.CatalogEntry
}

func LoadCatalog(path string) (*Index, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    var cat model.Catalog
    if err := json.Unmarshal(raw, &cat); err != nil {
        return nil, err
    }
    idx := &Index{
        byID:   make(map[string]model.CatalogEntry),
        byPath: make(map[string]model.CatalogEntry),
    }
    for path, entry := range cat.Binaries {
        key := strings.ToLower(entry.BuildID)
        idx.byID[key] = entry
        idx.byPath[path] = entry
    }
    return idx, nil
}

func (idx *Index) LookupBuildID(id string) (model.CatalogEntry, bool) {
    e, ok := idx.byID[strings.ToLower(id)]
    return e, ok
}

func (idx *Index) LookupPath(path string) (model.CatalogEntry, bool) {
    e, ok := idx.byPath[path]
    return e, ok
}

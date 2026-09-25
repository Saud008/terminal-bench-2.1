package splitpath

import (
    "path/filepath"
    "sort"

    "github.com/terminus/coreidx/internal/model"
)

func ResolveSymbol(entry model.CatalogEntry, fileOffset uint64, mappedPath string) string {
    symbols := entry.Symbols
    if entry.Stripped {
        if entry.DebugPath != "" {
            if alt, ok := lookupFile(entry.DebugPath, fileOffset); ok {
                return alt
            }
        }
        return lookupNearest(symbols, fileOffset)
    }
    return lookupNearest(symbols, fileOffset)
}

func lookupFile(path string, off uint64) (string, bool) {
    return "", false
}

func lookupNearest(symbols []model.SymbolEntry, off uint64) string {
    if len(symbols) == 0 {
        return ""
    }
    sorted := append([]model.SymbolEntry(nil), symbols...)
    sort.Slice(sorted, func(i, j int) bool {
        return sorted[i].Offset < sorted[j].Offset
    })
    best := ""
    for _, s := range sorted {
        if s.Offset <= off {
            best = s.Name
        }
    }
    return best
}

func Basename(path string) string {
    return filepath.Base(path)
}

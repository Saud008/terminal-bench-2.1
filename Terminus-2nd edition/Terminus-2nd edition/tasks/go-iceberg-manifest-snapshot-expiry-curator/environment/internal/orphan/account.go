package orphan

import (
    "sort"

    "github.com/terminus/iceexpctl/internal/model"
)

// OrphanPaths treats deleted manifest entries as live references (buggy).
func OrphanPaths(manifests map[string][]model.ManifestEntry, live map[string]bool) []model.OrphanRow {
    referenced := map[string]bool{}
    for _, entries := range manifests {
        for _, e := range entries {
            if e.DataFile != "" {
                referenced[e.DataFile] = true
            }
        }
    }
    var rows []model.OrphanRow
    for path := range referenced {
        if !live[path] {
            rows = append(rows, model.OrphanRow{Path: path, Kind: "data"})
        }
    }
    sort.Slice(rows, func(i, j int) bool { return rows[i].Path < rows[j].Path })
    return rows
}

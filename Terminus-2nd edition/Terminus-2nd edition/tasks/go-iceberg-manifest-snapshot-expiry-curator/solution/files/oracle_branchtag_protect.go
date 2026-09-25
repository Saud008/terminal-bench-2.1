package branchtag

import (
    "github.com/terminus/iceexpctl/internal/model"
    "github.com/terminus/iceexpctl/internal/snapgraph"
)

func ProtectedSet(table model.TableJSON) map[int64]bool {
    out := map[int64]bool{}
    for _, ref := range table.Refs {
        for _, sid := range snapgraph.Ancestors(table, ref.SnapshotID) {
            out[sid] = true
        }
    }
    return out
}

func RefNames(table model.TableJSON) []string {
    var names []string
    for _, ref := range table.Refs {
        names = append(names, ref.Name)
    }
    return names
}

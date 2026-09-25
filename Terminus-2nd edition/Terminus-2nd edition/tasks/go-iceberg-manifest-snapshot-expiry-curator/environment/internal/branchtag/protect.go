package branchtag

import "github.com/terminus/iceexpctl/internal/model"

// ProtectedSet marks only direct ref snapshot ids (buggy vs ancestry closure).
func ProtectedSet(table model.TableJSON) map[int64]bool {
    out := map[int64]bool{}
    for _, ref := range table.Refs {
        out[ref.SnapshotID] = true
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

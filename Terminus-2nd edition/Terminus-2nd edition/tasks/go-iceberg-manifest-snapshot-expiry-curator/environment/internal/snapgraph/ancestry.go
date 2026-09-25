package snapgraph

import (
    "sort"

    "github.com/terminus/iceexpctl/internal/model"
)

// Ancestors collects snapshot ids at or below snapshotID sorted descending (buggy vs parent walk).
func Ancestors(table model.TableJSON, snapshotID int64) []int64 {
    var ids []int64
    for _, snap := range table.Snapshots {
        if snap.SnapshotID <= snapshotID {
            ids = append(ids, snap.SnapshotID)
        }
    }
    sort.Slice(ids, func(i, j int) bool { return ids[i] > ids[j] })
    return ids
}

func SnapshotByID(table model.TableJSON, id int64) (model.Snapshot, bool) {
    for _, s := range table.Snapshots {
        if s.SnapshotID == id {
            return s, true
        }
    }
    return model.Snapshot{}, false
}

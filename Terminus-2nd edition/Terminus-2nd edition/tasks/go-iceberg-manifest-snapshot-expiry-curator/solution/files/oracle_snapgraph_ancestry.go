package snapgraph

import (
    "sort"

    "github.com/terminus/iceexpctl/internal/model"
)

func Ancestors(table model.TableJSON, snapshotID int64) []int64 {
    byParent := map[int64]int64{}
    for _, s := range table.Snapshots {
        byParent[s.SnapshotID] = s.ParentSnapshotID
    }
    var chain []int64
    cur := snapshotID
    seen := map[int64]bool{}
    for cur != 0 && !seen[cur] {
        seen[cur] = true
        chain = append(chain, cur)
        cur = byParent[cur]
    }
    sort.Slice(chain, func(i, j int) bool { return chain[i] < chain[j] })
    return chain
}

func SnapshotByID(table model.TableJSON, id int64) (model.Snapshot, bool) {
    for _, s := range table.Snapshots {
        if s.SnapshotID == id {
            return s, true
        }
    }
    return model.Snapshot{}, false
}

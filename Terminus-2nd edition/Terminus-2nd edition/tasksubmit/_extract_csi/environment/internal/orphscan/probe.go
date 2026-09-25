package orphscan

import (
    "sort"

    "github.com/terminus/snapretctl/internal/model"
    "github.com/terminus/snapretctl/internal/claimlnk"
)

func DanglingSnapshots(cluster model.ClusterJSON) []model.DanglingRow {
    jm := claimlnk.JoinMap(cluster)
    var rows []model.DanglingRow
    for _, snap := range cluster.Snapshots {
        if _, ok := jm[snap.SourcePVC]; ok {
            continue
        }
        rows = append(rows, model.DanglingRow{
            UID: snap.UID, Namespace: snap.Namespace,
            SourcePVC: snap.SourcePVC, Kind: "dangling",
        })
    }
    sort.Slice(rows, func(i, j int) bool {
        if rows[i].UID != rows[j].UID {
            return rows[i].UID < rows[j].UID
        }
        return rows[i].Namespace < rows[j].Namespace
    })
    return rows
}

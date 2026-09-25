package nsbkt

import (
    "sort"

    "github.com/terminus/snapretctl/internal/model"
)

func ProjectedBytes(cluster model.ClusterJSON, namespace string) int64 {
    var count int64
    for _, snap := range cluster.Snapshots {
        if snap.Namespace == namespace {
            count++
        }
    }
    return count
}

func QuotaViolations(cluster model.ClusterJSON) []model.QuotaViolation {
    var out []model.QuotaViolation
    for _, q := range cluster.Quotas {
        projected := ProjectedBytes(cluster, q.Namespace)
        if projected > q.MaxSnapshotBytes {
            out = append(out, model.QuotaViolation{
                Namespace: q.Namespace, ProjectedBytes: projected,
                MaxSnapshotBytes: q.MaxSnapshotBytes,
            })
        }
    }
    sort.Slice(out, func(i, j int) bool { return out[i].Namespace < out[j].Namespace })
    return out
}

package bprank

import (
    "os"
    "strconv"

    "github.com/terminus/snapretctl/internal/scdays"
    "github.com/terminus/snapretctl/internal/model"
    "github.com/terminus/snapretctl/internal/claimlnk"
)

const DefaultClusterRetentionDays = 30

func selectorMatchesNamespace(selector, namespace string) bool {
    if selector == "" {
        return true
    }
    return selector == namespace
}

func highestPriorityPolicy(policies []model.BackupPolicy, namespace string) (days int, found bool) {
    bestPri := -1
    for _, bp := range policies {
        if !selectorMatchesNamespace(bp.NamespaceSelector, namespace) {
            continue
        }
        if bp.Priority > bestPri {
            bestPri = bp.Priority
            days = bp.RetentionDays
            found = days > 0
        }
    }
    return days, found
}

func ClusterDefaultDays(cluster model.ClusterJSON) int {
    if raw := os.Getenv("TB3_CLUSTER_DEFAULT_RETENTION_DAYS"); raw != "" {
        if v, err := strconv.Atoi(raw); err == nil && v > 0 {
            return v
        }
    }
    if cluster.DefaultRetentionDays > 0 {
        return cluster.DefaultRetentionDays
    }
    return DefaultClusterRetentionDays
}

func RetentionDaysForSnapshot(cluster model.ClusterJSON, snap model.VolumeSnapshot) int {
    if snap.DeletionPolicy == "Retain" {
        return -1
    }
    if days, ok := highestPriorityPolicy(cluster.BackupPolicies, snap.Namespace); ok {
        return days
    }
    pvc, ok := claimlnk.SnapshotPVC(cluster, snap)
    if ok {
        if cd := scdays.ClassRetentionDays(cluster, pvc.StorageClassName); cd > 0 {
            return cd
        }
    }
    return ClusterDefaultDays(cluster)
}

func IsProtected(snap model.VolumeSnapshot, retentionDays int) bool {
    return snap.DeletionPolicy == "Retain" || retentionDays < 0
}

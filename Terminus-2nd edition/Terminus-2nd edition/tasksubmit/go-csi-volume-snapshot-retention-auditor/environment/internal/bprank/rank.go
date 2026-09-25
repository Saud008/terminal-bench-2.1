package bprank

import (
    "os"
    "strconv"

    "github.com/terminus/snapretctl/internal/scdays"
    "github.com/terminus/snapretctl/internal/model"
    "github.com/terminus/snapretctl/internal/claimlnk"
)

const DefaultClusterRetentionDays = 30

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
    pvc, ok := claimlnk.SnapshotPVC(cluster, snap)
    classDays := scdays.ClassRetentionDays(cluster, "")
    if ok {
        classDays = scdays.ClassRetentionDays(cluster, pvc.StorageClassName)
    }
    if classDays > 0 {
        return classDays
    }
    best := -1
    bestPri := -1
    for _, bp := range cluster.BackupPolicies {
        if bp.NamespaceSelector != "" && bp.NamespaceSelector != snap.Namespace {
            continue
        }
        if bp.Priority > bestPri {
            bestPri = bp.Priority
            best = bp.RetentionDays
        }
    }
    if best > 0 {
        return best
    }
    return ClusterDefaultDays(cluster)
}

func IsProtected(snap model.VolumeSnapshot, retentionDays int) bool {
    return snap.DeletionPolicy == "Retain" || retentionDays < 0
}

package model

type PVC struct {
    Namespace        string `json:"namespace"`
    Name             string `json:"name"`
    StorageClassName string `json:"storage_class_name"`
    RequestedBytes   int64  `json:"requested_bytes"`
}

type VolumeSnapshot struct {
    UID               string `json:"uid"`
    Namespace         string `json:"namespace"`
    Name              string `json:"name"`
    SourcePVC         string `json:"source_pvc"`
    RestoreSizeBytes  int64  `json:"restore_size_bytes"`
    DeletionPolicy    string `json:"deletion_policy"`
    CreationClock int64  `json:"creation_clock_ms"`
}

type StorageClass struct {
    Name          string `json:"name"`
    RetentionDays int    `json:"retention_days"`
}

type BackupPolicy struct {
    Name              string `json:"name"`
    Priority          int    `json:"priority"`
    RetentionDays     int    `json:"retention_days"`
    NamespaceSelector string `json:"namespace_selector"`
}

type NamespaceQuota struct {
    Namespace          string `json:"namespace"`
    MaxSnapshotBytes   int64  `json:"max_snapshot_bytes"`
    UsedSnapshotBytes  int64  `json:"used_snapshot_bytes"`
}

type ClusterJSON struct {
    AuditClockMs     int64            `json:"audit_clock_ms"`
    DefaultRetentionDays int              `json:"default_retention_days"`
    PVCs                 []PVC            `json:"pvcs"`
    Snapshots            []VolumeSnapshot `json:"snapshots"`
    StorageClasses       []StorageClass   `json:"storage_classes"`
    BackupPolicies       []BackupPolicy   `json:"backup_policies"`
    Quotas               []NamespaceQuota `json:"quotas"`
}

type FleetGraphFile struct {
    Engine        string      `json:"engine"`
    Scenario      string      `json:"scenario"`
    Cluster       ClusterJSON `json:"cluster"`
    FleetGraphDigest string      `json:"fleet_graph_digest"`
}

type Finding struct {
    Code      string `json:"code"`
    Snapshot  string `json:"snapshot_uid,omitempty"`
    Namespace string `json:"namespace,omitempty"`
    Detail    string `json:"detail"`
}

type AnalyzeFindings struct {
    Scenario     string    `json:"scenario"`
    FindingCount int       `json:"finding_count"`
    Findings     []Finding `json:"findings"`
}

type RevisionFile struct {
    AuditPassSeq int `json:"audit_pass_seq"`
}

type QuotaViolation struct {
    Namespace       string `json:"namespace"`
    ProjectedBytes  int64  `json:"projected_bytes"`
    MaxSnapshotBytes int64 `json:"max_snapshot_bytes"`
}

type RetentionReport struct {
    Scenario              string           `json:"scenario"`
    ProtectedCount          int              `json:"protected_count"`
    DeletableSnapshotUIDs   []string         `json:"deletable_snapshot_uids"`
    QuotaViolations         []QuotaViolation `json:"quota_violations"`
    ReportDigest            string           `json:"report_digest"`
}

type DanglingRow struct {
    UID       string `json:"uid"`
    Namespace string `json:"namespace"`
    SourcePVC string `json:"source_pvc"`
    Kind      string `json:"kind"`
}

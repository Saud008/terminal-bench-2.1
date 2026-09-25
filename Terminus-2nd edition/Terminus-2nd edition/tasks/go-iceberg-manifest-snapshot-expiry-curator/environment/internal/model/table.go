package model

type Snapshot struct {
    SnapshotID       int64  `json:"snapshot_id"`
    ParentSnapshotID int64  `json:"parent_snapshot_id"`
    EventMs          int64  `json:"event_ms"`
    ManifestList     string `json:"manifest_list"`
}

type Ref struct {
    Name       string `json:"name"`
    RefType    string `json:"ref_type"`
    SnapshotID int64  `json:"snapshot_id"`
}

type ManifestEntry struct {
    Status         string `json:"status"`
    DataFile       string `json:"data_file,omitempty"`
    ManifestPath   string `json:"manifest_path,omitempty"`
    NestedManifest string `json:"nested_manifest,omitempty"`
}

type TableJSON struct {
    TableName            string     `json:"table_name"`
    Location             string     `json:"location"`
    CurrentSnapshotID    int64      `json:"current_snapshot_id"`
    DeleteRetentionHours int64      `json:"delete_retention_hours"`
    Snapshots            []Snapshot `json:"snapshots"`
    Refs                 []Ref      `json:"refs"`
}

type CursorSnapshot struct {
    Engine        string                       `json:"engine"`
    Scenario      string                       `json:"scenario"`
    Table         TableJSON                    `json:"table"`
    Manifests     map[string][]ManifestEntry   `json:"manifests"`
    CursorSeal string                       `json:"cursor_seal"`
}

type Finding struct {
    Code       string `json:"code"`
    SnapshotID int64  `json:"snapshot_id,omitempty"`
    Detail     string `json:"detail"`
}

type AnalyzeFindings struct {
    Scenario     string    `json:"scenario"`
    FindingCount int       `json:"finding_count"`
    Findings     []Finding `json:"findings"`
}

type RevisionFile struct {
    AnalyzeRevision int `json:"analyze_revision"`
}

type ExpiryPlan struct {
    Scenario           string  `json:"scenario"`
    ProtectedCount     int     `json:"protected_count"`
    ExpiredSnapshotIDs []int64 `json:"expired_snapshot_ids"`
    PlanDigest         string  `json:"plan_digest"`
}

type OrphanRow struct {
    Path string `json:"path"`
    Kind string `json:"kind"`
}

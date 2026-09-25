package model

type SegmentRecord struct {
    Partition   int    `json:"partition"`
    Offset      int64  `json:"offset"`
    TimestampMs int64  `json:"timestamp_ms"`
    KeyRaw      string `json:"key_raw"`
    ValueRaw    string `json:"value_raw"`
    IsTombstone bool   `json:"is_tombstone"`
}

type StagedRecord struct {
    Partition      int    `json:"partition"`
    Offset         int64  `json:"offset"`
    TimestampMs    int64  `json:"timestamp_ms"`
    KeyRaw         string `json:"key_raw"`
    CanonicalKey   string `json:"canonical_key"`
    ValueRaw       string `json:"value_raw"`
    IsTombstone    bool   `json:"is_tombstone"`
}

type PartitionStaging struct {
    Engine        string         `json:"engine"`
    Topic         string         `json:"topic"`
    Scenario      string         `json:"scenario"`
    SegmentCount  int            `json:"segment_count"`
    RecordCount   int            `json:"record_count"`
    Records       []StagedRecord `json:"records"`
    StagingDigest string         `json:"staging_digest"`
}

type Finding struct {
    Code       string `json:"code"`
    Partition  int    `json:"partition"`
    Offset     int64  `json:"offset"`
    Detail     string `json:"detail"`
}

type ReconcileFindings struct {
    Scenario     string    `json:"scenario"`
    FindingCount int       `json:"finding_count"`
    Findings     []Finding `json:"findings"`
}

type CuratorSealFile struct {
    CuratorSeal int `json:"curator_seal"`
}

type SnapshotRow struct {
    CanonicalKey string `json:"canonical_key"`
    Partition    int    `json:"partition"`
    Offset       int64  `json:"offset"`
    ValueRaw     string `json:"value_raw"`
    Deleted      bool   `json:"deleted"`
}

type LineageRow struct {
    CanonicalKey string `json:"canonical_key"`
    Partition    int    `json:"partition"`
    Offset       int64  `json:"offset"`
    TimestampMs  int64  `json:"timestamp_ms"`
}

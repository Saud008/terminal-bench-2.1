package model

type PartMeta struct {
    PartID       string            `json:"part_id"`
    TableName    string            `json:"table_name"`
    PartitionKey map[string]string `json:"partition_key"`
    Detached     bool              `json:"detached"`
    PartCount    int               `json:"part_count"`
}

type MutCmd struct {
    MutationID      string `json:"mutation_id"`
    PartitionID     string `json:"partition_id"`
    MutationVersion int    `json:"mutation_version"`
    Command         string `json:"command"`
    IssuedAt        string `json:"issued_at"`
}

type ReplicaLog struct {
    ReplicaName    string `json:"replica_name"`
    PartitionID    string `json:"partition_id"`
    LagSec         int    `json:"lag_sec"`
    LastMutationID string `json:"last_mutation_id"`
}

type LagPolicy struct {
    MaxLagSec int `json:"max_lag_sec"`
}

type Catalog struct {
    Tables map[string]struct {
        PartitionColumns []string `json:"partition_columns"`
    } `json:"tables"`
}

type Config struct {
    Lag   LagPolicy
    Cat   Catalog
    Anchor string
}

type StagedMutation struct {
    MutationID      string `json:"mutation_id"`
    PartitionID     string `json:"partition_id"`
    MutationVersion int    `json:"mutation_version"`
    TableName       string `json:"table_name"`
    ReadinessState  string `json:"readiness_state"`
    ReplicaLagMax   int    `json:"replica_lag_max"`
    PartCount       int    `json:"part_count"`
    IssuedAt        string `json:"issued_at"`
}

type ReadinessReport struct {
    AnchorUTC string           `json:"anchor_utc"`
    Mutations []StagedMutation `json:"mutations"`
    Totals    ReadinessTotals  `json:"totals"`
}

type ReadinessTotals struct {
    MutationCount   int `json:"mutation_count"`
    ReadyCount      int `json:"ready_count"`
    SuppressedCount int `json:"suppressed_count"`
    DetachedCount   int `json:"detached_count"`
}

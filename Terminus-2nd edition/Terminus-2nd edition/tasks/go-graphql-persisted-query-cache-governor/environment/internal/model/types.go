package model

type OperationManifest struct {
	OperationID      string `json:"operation_id"`
	OperationHash    string `json:"operation_hash"`
	SchemaHash       string `json:"schema_hash"`
	QueryText        string `json:"query_text"`
	RegisteredAtMs   int64  `json:"registered_at_ms"`
	LastSeenMs       int64  `json:"last_seen_ms"`
	ManifestVersion  int    `json:"manifest_version"`
}

type StagedOperation struct {
	OperationID      string `json:"operation_id"`
	OperationHash    string `json:"operation_hash"`
	SchemaHash       string `json:"schema_hash"`
	RegisteredAtMs   int64  `json:"registered_at_ms"`
	LastSeenMs       int64  `json:"last_seen_ms"`
}

type PQStaging struct {
	Engine         string            `json:"engine"`
	TenantID       string            `json:"tenant_id"`
	Scenario       string            `json:"scenario"`
	SchemaHash     string            `json:"schema_hash"`
	OperationCount int               `json:"operation_count"`
	Operations     []StagedOperation `json:"operations"`
	StagingDigest  string            `json:"staging_digest"`
}

type ApqAuditSeq struct {
	ApqAuditSeq int `json:"apq_audit_seq"`
}

type ReconcileReport struct {
	TenantID           string `json:"tenant_id"`
	Scenario           string `json:"scenario"`
	SchemaHash         string `json:"schema_hash"`
	ActiveCount        int    `json:"active_count"`
	EvictedCount       int    `json:"evicted_count"`
	QuotaMax           int    `json:"quota_max"`
	QuotaHeadroom      int    `json:"quota_headroom"`
	ApqAuditSeq  int    `json:"apq_audit_seq"`
}

type LedgerOperation struct {
	OperationID    string
	TenantID       string
	OperationHash  string
	SchemaHash     string
	Status         string
	RegisteredAtMs int64
	LastSeenMs     int64
}

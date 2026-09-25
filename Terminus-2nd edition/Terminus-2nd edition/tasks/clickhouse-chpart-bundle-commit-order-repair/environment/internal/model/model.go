package model

type PartMeta struct {
	PartID    string `json:"part_id"`
	BatchID   string `json:"batch_id"`
	Checksum  string `json:"checksum"`
	MinBlock  int64  `json:"min_block"`
	MaxBlock  int64  `json:"max_block"`
	Table     string `json:"table"`
}

type Row struct {
	ID       string `json:"id"`
	Ver      int64  `json:"ver"`
	Value    string `json:"value"`
	ExpireTS int64  `json:"expire_ts"`
	PartID   string `json:"part_id"`
}

type MergedRow struct {
	ID       string `json:"id"`
	Ver      int64  `json:"ver"`
	Value    string `json:"value"`
	ExpireTS int64  `json:"expire_ts"`
}

type PartStats struct {
	PartID      string `json:"part_id"`
	RowCount    int    `json:"row_count"`
	ChecksumOK  bool   `json:"checksum_ok"`
	Committed   bool   `json:"committed"`
}

type Snapshot struct {
	TableSuffix   string      `json:"table_suffix"`
	TableName     string      `json:"table_name"`
	MaxBlock      int64       `json:"max_block_number"`
	Fsynced       bool        `json:"fsynced"`
	Parts         []PartStats `json:"parts"`
	Rows          []MergedRow `json:"rows"`
	IdempotentKey string      `json:"idempotency_key"`
}

type ExportReport struct {
	TableName string      `json:"table_name"`
	MaxBlock  int64       `json:"max_block_number"`
	RowCount  int         `json:"row_count"`
	Rows      []MergedRow `json:"rows"`
	Parts     []PartStats `json:"parts"`
}

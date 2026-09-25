package model

type Catalog struct {
	Table     string     `json:"table"`
	CatalogTZ string     `json:"catalog_tz"`
	ChunkSize int        `json:"chunk_size"`
	RowGroups []RowGroup `json:"row_groups"`
}

type RowGroup struct {
	ID      int               `json:"id"`
	Rows    []Row             `json:"rows"`
	Columns map[string]Column `json:"columns"`
}

type Column struct {
	StatsPresent     bool     `json:"stats_present"`
	NullCount        int      `json:"null_count"`
	NullCountOmitted bool     `json:"null_count_omitted"`
	Min              string   `json:"min,omitempty"`
	Max              string   `json:"max,omitempty"`
	PageOrder        []string `json:"page_order"`
	ChunkSize        int      `json:"chunk_size"`
}

type Row struct {
	RowID      int     `json:"_row_id"`
	SensorID   *string `json:"sensor_id"`
	MeasuredAt string  `json:"measured_at"`
	HiddenFlag *bool   `json:"hidden_flag,omitempty"`
	Note       string  `json:"note,omitempty"`
}

type FilterSpec struct {
	IsNullCol string
	TsGte     string
	Workers   int
}

type PushdownPlan struct {
	Table          string   `json:"table"`
	SelectedGroups []int    `json:"selected_row_groups"`
	PageReadOrder  []string `json:"page_read_order"`
	WorkerSlices   [][]int  `json:"worker_slices"`
	PlanWritten    bool     `json:"plan_written"`
}

type FilterResult struct {
	Table           string `json:"table"`
	MatchedRowIDs   []int  `json:"matched_row_ids"`
	RowCount        int    `json:"row_count"`
	PrunedRowGroups []int  `json:"pruned_row_groups"`
	PlanChecksum    string `json:"plan_checksum"`
}

package model

type Config struct {
	Seed             string                       `json:"seed"`
	FlushIntervalSec int64                        `json:"flush_interval_sec"`
	EpochOrigin      int64                        `json:"epoch_origin"`
	TimeSkewSec      int64                        `json:"time_skew_sec"`
	TypesDB          map[string]map[string]string `json:"types_db"`
	Batches          []string                     `json:"batches"`
}

type RawReading struct {
	Identifier string
	Interval   int64
	Groups     []ValueGroup
	LineNo     int
}

type ValueGroup struct {
	Epoch  int64
	Values []float64
}

type NormalizedPoint struct {
	CanonicalID string
	DS          string
	ValueKind   string
	Epoch       int64
	Value       float64
}

type MetricExport struct {
	CanonicalID string  `json:"canonical_id"`
	DS          string  `json:"ds"`
	ValueKind   string  `json:"value_kind"`
	Epoch       int64   `json:"epoch"`
	Value       float64 `json:"value"`
}

type FlushExport struct {
	FlushIndex int            `json:"flush_index"`
	StartEpoch int64          `json:"start_epoch"`
	EndEpoch   int64          `json:"end_epoch"`
	Metrics    []MetricExport `json:"metrics"`
}

type Stats struct {
	Lines    int `json:"lines"`
	Accepted int `json:"accepted"`
	Rejected int `json:"rejected"`
}

type Report struct {
	PipelineVersion int           `json:"pipeline_version"`
	Seed            string        `json:"seed"`
	Batches         []string      `json:"batches"`
	Flushes         []FlushExport `json:"flushes"`
	Stats           Stats         `json:"stats"`
}

package model

type LabelPair struct {
	Name  string `json:"name"`
	Value string `json:"value"`
}

type Exemplar struct {
	LE      string  `json:"le"`
	TraceID string  `json:"trace_id"`
	Value   float64 `json:"value"`
}

type Bucket struct {
	LE              string `json:"le"`
	Count           uint64 `json:"count"`
	ExemplarTraceID string `json:"exemplar_trace_id,omitempty"`
}

type Series struct {
	Labels          []LabelPair `json:"labels"`
	HistogramSchema int         `json:"histogram_schema"`
	CounterReset    bool        `json:"counter_reset"`
	Buckets         []Bucket    `json:"buckets"`
	Exemplars       []Exemplar  `json:"exemplars"`
}

type WriteRequest struct {
	Seed   string   `json:"seed"`
	Series []Series `json:"series"`
}

type SnapshotSeries struct {
	Labels          map[string]string `json:"labels"`
	HistogramSchema int               `json:"histogram_schema"`
	Buckets         []Bucket          `json:"buckets"`
}

type Snapshot struct {
	Seed     string           `json:"seed"`
	Sequence int              `json:"sequence"`
	Series   []SnapshotSeries `json:"series"`
}

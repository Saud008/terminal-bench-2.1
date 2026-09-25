package model

type Sample struct {
	Metric      string
	Labels      string
	Kind        string
	Value       float64
	TsMs        int64
	ScrapeOrder int
}

type HistBucket struct {
	Metric      string
	Labels      string
	Le          string
	Count       float64
	TsMs        int64
	ScrapeOrder int
}

type Bucket struct {
	Le    string  `json:"le"`
	Count float64 `json:"count"`
}

type SeriesRollup struct {
	Metric         string   `json:"metric"`
	Labels         string   `json:"labels"`
	WindowStartMs  int64    `json:"window_start_ms"`
	WindowEndMs    int64    `json:"window_end_ms"`
	Tier           string   `json:"tier"`
	Kind           string   `json:"kind"`
	Value          float64  `json:"value"`
	RatePerSec     float64  `json:"rate_per_sec"`
	Stale          bool     `json:"stale"`
	Buckets        []Bucket `json:"buckets,omitempty"`
}

type RollupSnapshot struct {
	SchemaVersion int            `json:"schema_version"`
	GeneratedAtMs int64          `json:"generated_at_ms"`
	Series        []SeriesRollup `json:"series"`
}

type ScrapeManifest struct {
	SchemaVersion       int    `json:"schema_version"`
	ScrapesIngested     int    `json:"scrapes_ingested"`
	LastScrapeTsMs      int64  `json:"last_scrape_ts_ms"`
	SamplesAccepted     int    `json:"samples_accepted"`
	CacheEntries        int    `json:"cache_entries"`
	RollupWindowsBuilt  int    `json:"rollup_windows_built"`
	StalenessMarkers    int    `json:"staleness_markers"`
	ManifestSha256      string `json:"manifest_sha256"`
}

type QueryReport struct {
	Metric               string       `json:"metric"`
	WindowStartMs        int64        `json:"window_start_ms"`
	WindowEndMs          int64        `json:"window_end_ms"`
	ServedFromCache      bool         `json:"served_from_cache"`
	FreshRawWithinGrace  bool         `json:"fresh_raw_within_grace"`
	QueryMs              int64        `json:"query_ms"`
	Rollup               SeriesRollup `json:"rollup"`
}

type CacheEntry struct {
	Key            string
	Metric         string
	Labels         string
	WindowStartMs  int64
	WindowEndMs    int64
	LastSampleTsMs int64
	CreatedWallMs  int64
	Rollup         SeriesRollup
}

type IngestStats struct {
	LinesRead          int
	SamplesAccepted    int
	ScrapesIngested    int
	CacheEntries       int
	RollupWindows      int
	StalenessMarkers   int
}

package model

type KeyRange struct {
	Start string `json:"start"`
	End   string `json:"end"`
}

type Shard struct {
	Name     string   `json:"name"`
	KeyRange KeyRange `json:"key_range"`
}

type ShardMap struct {
	Generation int     `json:"generation"`
	Shards     []Shard `json:"shards"`
}

type VindexDef struct {
	Name   string            `json:"name"`
	Type   string            `json:"type"`
	Params map[string]string `json:"params"`
}

type VindexCatalog struct {
	Vindexes []VindexDef `json:"vindexes"`
}

type CacheEntry struct {
	VindexName string `json:"vindex_name"`
	KeyHex     string `json:"key_hex"`
	Shard      string `json:"shard"`
	Generation int    `json:"generation"`
}

type Query struct {
	Vindex string `json:"vindex"`
	Key    string `json:"key"`
}

type RouteBatch struct {
	Queries []Query `json:"queries"`
}

type RouteResult struct {
	Vindex string `json:"vindex"`
	Key    string `json:"key"`
	Shard  string `json:"shard"`
	From   string `json:"from"`
}

type RoutePlan struct {
	Generation int           `json:"generation"`
	Routes     []RouteResult `json:"routes"`
	CacheHits  int           `json:"cache_hits"`
	ScatterOK  bool          `json:"scatter_ok"`
}

type Snapshot struct {
	Generation      int          `json:"generation"`
	ShardMapPath    string       `json:"shard_map_path"`
	Vindexes        []VindexDef  `json:"vindexes"`
	Cache           []CacheEntry `json:"cache"`
	MigrationID     string       `json:"migration_id"`
	CoalesceDropped int          `json:"coalesce_dropped"`
}

type MigrationEvent struct {
	Seq        int    `json:"seq"`
	Op         string `json:"op"`
	ShardMap   string `json:"shard_map,omitempty"`
	Migration  string `json:"migration_id,omitempty"`
}

type RoutingAudit struct {
	Generation      int            `json:"generation"`
	SnapshotPath    string         `json:"snapshot_path"`
	RouteCount      int            `json:"route_count"`
	CacheHitCount   int            `json:"cache_hit_count"`
	CoalesceDropped int            `json:"coalesce_dropped"`
	ScatterFailures int            `json:"scatter_failures"`
	ShardCounts     map[string]int `json:"shard_counts"`
}

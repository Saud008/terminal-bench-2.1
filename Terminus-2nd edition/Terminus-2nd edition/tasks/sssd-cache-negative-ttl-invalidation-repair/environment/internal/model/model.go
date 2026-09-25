package model

type Op struct {
	TS     int64  `json:"ts"`
	Seq    int    `json:"seq"`
	Kind   string `json:"kind"`
	Domain string `json:"domain"`
	Name   string `json:"name"`
	Group  string `json:"group"`
	Member string `json:"member"`
	Value  string `json:"value"`
}

type Stats struct {
	LinesRead            int `json:"lines_read"`
	OpsApplied           int `json:"ops_applied"`
	ParseErrors          int `json:"parse_errors"`
	LookupMiss           int `json:"lookup_miss"`
	LookupHit            int `json:"lookup_hit"`
	CachePut             int `json:"cache_put"`
	CacheDel             int `json:"cache_del"`
	NegativeCreated      int `json:"negative_created"`
	NegativeRefreshed    int `json:"negative_refreshed"`
	GroupAddMember       int `json:"group_add_member"`
	GroupInvalidations   int `json:"group_invalidations"`
	ExplicitInvalidation int `json:"explicit_invalidation"`
	WALCheckpoints       int `json:"wal_checkpoints"`
}

type NegativeExport struct {
	Domain    string `json:"domain"`
	Name      string `json:"name"`
	MissTS    int64  `json:"miss_ts"`
	ExpiresAt int64  `json:"expires_at"`
}

type PositiveExport struct {
	Domain string `json:"domain"`
	Name   string `json:"name"`
	Value  string `json:"value"`
}

type GroupExport struct {
	Group   string   `json:"group"`
	Members []string `json:"members"`
}

type Snapshot struct {
	SnapshotVersion int              `json:"snapshot_version"`
	DomainSuffix    string           `json:"domain_suffix"`
	EvaluatedAtMS   int64            `json:"evaluated_at_ms"`
	Negatives       []NegativeExport `json:"negatives"`
	Positives       []PositiveExport `json:"positives"`
	Groups          []GroupExport    `json:"groups"`
	Stats           Stats            `json:"stats"`
}

type CacheReport struct {
	DomainSuffix    string           `json:"domain_suffix"`
	ActiveNegatives []NegativeExport `json:"active_negatives"`
	Positives       []PositiveExport `json:"positives"`
	Stats           Stats            `json:"stats"`
}

type NegativeEntry struct {
	Domain    string
	Name      string
	MissTS    int64
	ExpiresAt int64
}

type PrincipalMeta struct {
	Domain string
	Name   string
}

type CacheState struct {
	DomainSuffix string
	Negatives    map[string]*NegativeEntry
	Positives    map[string]string
	PrincipalMeta map[string]PrincipalMeta
	Groups       map[string]map[string]bool
	LastTS       int64
}

func NewCacheState(domainSuffix string) *CacheState {
	return &CacheState{
		DomainSuffix:  domainSuffix,
		Negatives:     map[string]*NegativeEntry{},
		Positives:     map[string]string{},
		PrincipalMeta: map[string]PrincipalMeta{},
		Groups:        map[string]map[string]bool{},
	}
}

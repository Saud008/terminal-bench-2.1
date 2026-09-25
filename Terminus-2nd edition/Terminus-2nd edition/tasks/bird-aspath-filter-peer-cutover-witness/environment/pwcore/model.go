package pwcore

type Filter struct {
	FilterID  string `json:"filter_id"`
	Priority  int    `json:"priority"`
	MatchMode string `json:"match_mode"`
	Action    string `json:"action"`
	ASN       int    `json:"asn,omitempty"`
	ASPath    []int  `json:"as_path,omitempty"`
}

type PeerGroup struct {
	GroupID string   `json:"group_id"`
	Filters []Filter `json:"filters"`
}

type Peer struct {
	PeerID               string            `json:"peer_id"`
	ASN                  int               `json:"asn"`
	GroupID              string            `json:"group_id"`
	WaveRank             int               `json:"wave_rank"`
	MedCeiling           *int              `json:"med_ceiling"`
	AbortOnCriticalDeny  bool              `json:"abort_on_critical_deny"`
	CommunityRewrite     map[string]string `json:"community_rewrite"`
	Filters              []Filter          `json:"filters"`
}

type Route struct {
	Prefix      string   `json:"prefix"`
	ASPath      []int    `json:"as_path"`
	Communities []string `json:"communities"`
	Med         int      `json:"med"`
	PeerID      string   `json:"peer_id"`
}

type Inventory struct {
	Scenario          string      `json:"scenario"`
	CriticalPrefixes  []string    `json:"critical_prefixes"`
	PeerGroups        []PeerGroup `json:"peer_groups"`
	Peers             []Peer      `json:"peers"`
	RIB               []Route     `json:"rib"`
	RunID             string      `json:"run_id,omitempty"`
}

type Row struct {
	PeerID         string   `json:"peer_id"`
	Prefix         string   `json:"prefix"`
	Action         string   `json:"action"`
	ASPath         []int    `json:"as_path"`
	Communities    []string `json:"communities"`
	Med            int      `json:"med"`
	MatchedFilter  *string  `json:"matched_filter"`
	Aborted        bool     `json:"aborted"`
}

type Ledger struct {
	SchemaVersion int     `json:"schema_version"`
	RunID         string  `json:"run_id"`
	WaveAborted   bool    `json:"wave_aborted"`
	PeerOrder     []string `json:"peer_order"`
	Rows          []Row   `json:"rows"`
	RIBAfter      []Route `json:"rib_after"`
}

type Report struct {
	SchemaVersion int      `json:"schema_version"`
	RunID         string   `json:"run_id"`
	WaveAborted   bool     `json:"wave_aborted"`
	PeerOrder     []string `json:"peer_order"`
	Rows          []Row    `json:"rows"`
	AuditDigest   string   `json:"audit_digest"`
}

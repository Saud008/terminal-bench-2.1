package types

// MatcherBlock is one Caddy-style matcher clause in staging.
type MatcherBlock struct {
	Path       []string          `json:"path,omitempty"`
	PathRegexp []string          `json:"path_regexp,omitempty"`
	Header     map[string][]string `json:"header,omitempty"`
	Method     []string          `json:"method,omitempty"`
}

// RouteRow is a normalized route in staging.
type RouteRow struct {
	Index      int            `json:"index"`
	HandlerID  string         `json:"handler_id"`
	Group      string         `json:"group"`
	Terminal   bool           `json:"terminal"`
	HandlePath bool           `json:"handle_path"`
	Matchers   []MatcherBlock `json:"matchers"`
	Source     string         `json:"source"`
}

// StageFile is the on-disk staging snapshot.
type StageFile struct {
	Routes    []RouteRow `json:"routes"`
	IngestSeq int        `json:"ingest_seq"`
}

// CommitFile tracks replay sequence across ingest cycles.
type CommitFile struct {
	ReplaySeq int    `json:"replay_seq"`
	StageHash string `json:"stage_hash"`
}

// LastMatch is written by match subcommand.
type LastMatch struct {
	Matched   bool   `json:"matched"`
	HandlerID string `json:"handler_id"`
	RouteIdx  int    `json:"route_index"`
}

// RouteConfig is raw JSON from ingest input files.
type RouteConfig struct {
	Routes []struct {
		ID         string         `json:"id"`
		Group      string         `json:"group"`
		Terminal   bool           `json:"terminal"`
		HandlePath bool           `json:"handle_path"`
		Match      []MatcherBlock `json:"match"`
	} `json:"routes"`
}

package model

type Request struct {
	Sub string `json:"sub"`
	Dom string `json:"dom"`
	Obj string `json:"obj"`
	Act string `json:"act"`
}

type Policy struct {
	Priority int
	Sub      string
	Dom      string
	Obj      string
	Act      string
	Eft      string
}

type Grouping struct {
	Child  string
	Parent string
	Dom    string
}

type Result struct {
	Sub        string `json:"sub"`
	Dom        string `json:"dom"`
	Obj        string `json:"obj"`
	Act        string `json:"act"`
	Decision   string `json:"decision"`
	MatchCount int    `json:"match_count"`
}

type Stats struct {
	Requests        int `json:"requests"`
	Allows          int `json:"allows"`
	Denies          int `json:"denies"`
	PoliciesLoaded  int `json:"policies_loaded"`
	GroupingsLoaded int `json:"groupings_loaded"`
}

type Report struct {
	Model       string   `json:"model"`
	Bundles     []string `json:"bundles"`
	Results     []Result `json:"results"`
	Stats       Stats    `json:"stats"`
	AuditDigest string   `json:"audit_digest"`
}

type Engine struct {
	Policies  []Policy
	Groupings []Grouping
}

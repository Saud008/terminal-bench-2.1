package model

type Snapshot struct {
    Version   string        `json:"version"`
    Listeners []Listener    `json:"listeners"`
    Routes    []RouteGroup  `json:"routes"`
    Clusters  []Cluster     `json:"clusters"`
    Secrets   []SecretEntry `json:"secrets"`
}

type Listener struct {
    Name         string        `json:"name"`
    FilterChains []FilterChain `json:"filter_chains"`
}

type FilterChain struct {
    Filters []Filter `json:"filters"`
}

type Filter struct {
    Name string `json:"name"`
    Type string `json:"type"`
}

type RouteGroup struct {
    Domain string      `json:"domain"`
    Routes []RouteRule `json:"routes"`
}

type RouteRule struct {
    Match      RouteMatch `json:"match"`
    Cluster    string     `json:"cluster"`
    Precedence int        `json:"precedence"`
}

type RouteMatch struct {
    Prefix string `json:"prefix,omitempty"`
    Path   string `json:"path,omitempty"`
}

type Cluster struct {
    Name      string     `json:"name"`
    Endpoints []Endpoint `json:"endpoints"`
}

type Endpoint struct {
    Host   string `json:"host"`
    Weight int    `json:"weight"`
}

type SecretEntry struct {
    Name     string `json:"name"`
    SecretID string `json:"secret_id"`
}

type StagingFile struct {
    Engine        string   `json:"engine"`
    Scenario      string   `json:"scenario"`
    Left          Snapshot `json:"left"`
    Right         Snapshot `json:"right"`
    StagingDigest string   `json:"staging_digest"`
}

type RevisionFile struct {
    NormalizeRevision int `json:"normalize_revision"`
}

type DiffChange struct {
    Path       string `json:"path"`
    ChangeType string `json:"change_type"`
    LeftValue  string `json:"left_value,omitempty"`
    RightValue string `json:"right_value,omitempty"`
}

type DiffReport struct {
    Scenario     string       `json:"scenario"`
    ChangeCount  int          `json:"change_count"`
    Changes      []DiffChange `json:"changes"`
    ReportDigest string       `json:"report_digest"`
}

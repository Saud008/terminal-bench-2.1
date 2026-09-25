package model

type Party struct {
    ID      string   `json:"id"`
    Name    string   `json:"name"`
    Aliases []string `json:"aliases"`
}

type AliasEdge struct {
    From string `json:"from"`
    To   string `json:"to"`
}

type Docket struct {
    Number    string `json:"number"`
    FiledAt   string `json:"filed_at"`
    PrimaryFlag bool   `json:"primary_flag"`
}

type PageLine struct {
    LineNum int    `json:"line_num"`
    Text    string `json:"text"`
}

type Page struct {
    PageNum int        `json:"page_num"`
    Lines   []PageLine `json:"lines"`
}

type SealedTerm struct {
    Term string `json:"term"`
}

type Policy struct {
    CourtID      string `json:"court_id"`
    RiskFloor    string `json:"risk_floor"`
    SealedStrict bool   `json:"sealed_strict"`
}

type BundleStage struct {
    Engine        string       `json:"engine"`
    Scenario      string       `json:"scenario"`
    Dockets       []Docket     `json:"dockets"`
    Parties       []Party      `json:"parties"`
    Pages         []Page       `json:"pages"`
    SealedTerms   []SealedTerm `json:"sealed_terms"`
    Policy        Policy       `json:"policy"`
    BundleDigest  string       `json:"bundle_digest"`
}

type PartyGraph struct {
    Scenario string              `json:"scenario"`
    Nodes    []string            `json:"nodes"`
    Edges    []AliasEdge         `json:"edges"`
    Resolved map[string][]string `json:"resolved_aliases"`
}

type IndexRevision struct {
    IndexRevision int `json:"index_revision"`
}

type RiskFinding struct {
    FindingID  string `json:"finding_id"`
    PartyID    string `json:"party_id"`
    ExhibitRef string `json:"exhibit_ref"`
    Term       string `json:"term"`
    RiskLevel  string `json:"risk_level"`
    Page       int    `json:"page"`
    Line       int    `json:"line"`
    Docket     string `json:"docket"`
}

type FindingsFile struct {
    Scenario string        `json:"scenario"`
    Findings []RiskFinding `json:"findings"`
}

type AtlasReport struct {
    Scenario      string        `json:"scenario"`
    FindingCount  int           `json:"finding_count"`
    Findings      []RiskFinding `json:"findings"`
    AtlasDigest   string        `json:"atlas_digest"`
}

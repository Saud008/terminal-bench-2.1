package model

type SurveyState string

const (
	StateWaiting   SurveyState = "waiting"
	StateCollect   SurveyState = "collecting"
	StateDeadline  SurveyState = "deadline"
	StateClosed    SurveyState = "closed"
)

type Topology struct {
	Kind  string     `json:"kind"`
	Hub   string     `json:"hub"`
	Edges [][2]string `json:"edges"`
}

type MeshEvent struct {
	OffsetMS   int    `json:"offset_ms"`
	Type       string `json:"type"`
	Respondent string `json:"respondent,omitempty"`
	Vote       int    `json:"vote,omitempty"`
	HeaderHex  string `json:"header_hex,omitempty"`
}

type Mesh struct {
	MeshID       string      `json:"mesh_id"`
	SurveyID     string      `json:"survey_id"`
	DeadlineMS   int         `json:"deadline_ms"`
	DefaultTTLMS int         `json:"default_ttl_ms"`
	Topology     Topology    `json:"topology"`
	Events       []MeshEvent `json:"events"`
}

type TallyRecord struct {
	EventIndex       int    `json:"event_index"`
	OffsetMS         int    `json:"offset_ms"`
	EventType        string `json:"event_type"`
	Respondent       string `json:"respondent,omitempty"`
	SurveyIDHeader   string `json:"survey_id_header,omitempty"`
	SurveyIDOK       bool   `json:"survey_id_ok"`
	PipeDrained      bool   `json:"pipe_drained"`
	Sealed           bool   `json:"sealed"`
	TTLExpiresMS     int    `json:"ttl_expires_ms,omitempty"`
	ReconnectReset   bool   `json:"reconnect_reset"`
	TallyIncluded    bool   `json:"tally_included"`
	TopologyWeight   int    `json:"topology_weight,omitempty"`
	StateAfter       string `json:"state_after,omitempty"`
	RejectReason     string `json:"reject_reason,omitempty"`
}

type SurveySnapshot struct {
	SnapshotVersion    int            `json:"snapshot_version"`
	TableSuffix        string         `json:"table_suffix"`
	MeshID             string         `json:"mesh_id"`
	SurveyID           string         `json:"survey_id"`
	Records            []TallyRecord  `json:"records"`
	FinalTally         map[string]int `json:"final_tally"`
	TotalWeighted      int            `json:"total_weighted"`
	PartialRespondents []string       `json:"partial_respondents"`
	ExportReady        bool           `json:"export_ready"`
}

type SurveyReport struct {
	ReportVersion      int            `json:"report_version"`
	TableSuffix        string         `json:"table_suffix"`
	MeshID             string         `json:"mesh_id"`
	SurveyID           string         `json:"survey_id"`
	Records            []TallyRecord  `json:"records"`
	FinalTally         map[string]int `json:"final_tally"`
	TotalWeighted      int            `json:"total_weighted"`
	PartialRespondents []string       `json:"partial_respondents"`
	ExportSource       string         `json:"export_source"`
}

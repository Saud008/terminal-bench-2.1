package model

// Tuple is a relationship record stored at a revision.
type Tuple struct {
	Namespace  string  `json:"namespace"`
	Object     string  `json:"object"`
	Relation   string  `json:"relation"`
	Subject    string  `json:"subject"`
	CaveatExpr *string `json:"caveat_expr,omitempty"`
}

// TupleWriteRequest is POST /v1/tuple/write body.
type TupleWriteRequest struct {
	Operation  string  `json:"operation"`
	Namespace  string  `json:"namespace"`
	Object     string  `json:"object"`
	Relation   string  `json:"relation"`
	Subject    string  `json:"subject"`
	CaveatExpr *string `json:"caveat_expr,omitempty"`
}

// CheckRequest is POST /v1/check body.
type CheckRequest struct {
	Namespace string `json:"namespace"`
	Object    string `json:"object"`
	Relation  string `json:"relation"`
	Subject   string `json:"subject"`
	ZedToken  string `json:"zed_token"`
}

// CheckResponse is POST /v1/check response.
type CheckResponse struct {
	Allowed   bool   `json:"allowed"`
	Revision  int64  `json:"revision"`
	ZedToken  string `json:"zed_token"`
	UsedStale bool   `json:"used_stale_snapshot"`
}

// WatchRequest is POST /v1/watch body.
type WatchRequest struct {
	NamespaceFilter string `json:"namespace_filter"`
	AfterRevision   int64  `json:"after_revision"`
	Limit           int    `json:"limit"`
}

// WatchEvent is one revision log event delivered to clients.
type WatchEvent struct {
	Revision  int64  `json:"revision"`
	Namespace string `json:"namespace"`
	Op        string `json:"op"`
	Object    string `json:"object"`
	Relation  string `json:"relation"`
	Subject   string `json:"subject"`
}

// WatchResponse is POST /v1/watch response.
type WatchResponse struct {
	Events         []WatchEvent `json:"events"`
	NextCursor     int64        `json:"next_cursor"`
	FilteredSkips  int          `json:"filtered_skips"`
}

// ExportRequest is POST /v1/export body.
type ExportRequest struct {
	Force bool `json:"force"`
}

// ExportResponse is POST /v1/export response.
type ExportResponse struct {
	Path     string `json:"path"`
	Revision int64  `json:"revision"`
	Checks   int    `json:"checks"`
}

// SeedRequest loads fixture tuples for admin bootstrap.
type SeedRequest struct {
	Fixture string `json:"fixture"`
}

// RevisionSnapshot is persisted at /app/state/revision-snapshot.json after writes.
type RevisionSnapshot struct {
	Revision       int64            `json:"revision"`
	TupleCount     int              `json:"tuple_count"`
	Namespaces     []string         `json:"namespaces"`
	CheckSummaries []CheckSummary   `json:"check_summaries"`
	Tuples         []SnapshotTuple  `json:"tuples"`
}

// SnapshotTuple is a tuple row at snapshot revision.
type SnapshotTuple struct {
	Namespace  string  `json:"namespace"`
	Object     string  `json:"object"`
	Relation   string  `json:"relation"`
	Subject    string  `json:"subject"`
	CaveatExpr *string `json:"caveat_expr,omitempty"`
	Active     bool    `json:"active"`
}

// CheckSummary records a probe check embedded in the snapshot.
type CheckSummary struct {
	Namespace string `json:"namespace"`
	Object    string `json:"object"`
	Relation  string `json:"relation"`
	Subject   string `json:"subject"`
	Allowed   bool   `json:"allowed"`
}

// AuthzReport is written to /app/output/authz-report.json.
type AuthzReport struct {
	GeneratedRevision int64          `json:"generated_revision"`
	SnapshotRevision  int64          `json:"snapshot_revision"`
	NamespaceCounts   map[string]int `json:"namespace_counts"`
	AllowedChecks     []CheckSummary `json:"allowed_checks"`
	DeniedChecks      []CheckSummary `json:"denied_checks"`
	TupleTotal        int            `json:"tuple_total"`
}

// CaveatExpr is the JSON shape inside caveat_expr strings.
type CaveatExpr struct {
	AllowSubject string `json:"allow_subject"`
}

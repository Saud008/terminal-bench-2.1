package model

// Entry is one LDAP shadow directory entry.
type Entry struct {
	NormalizedDN string            `json:"normalized_dn"`
	Attrs        map[string]string `json:"attrs"`
	USNChanged   int64             `json:"usn_changed"`
}

// StagedChange is one applied changelog row written to staging JSONL.
type StagedChange struct {
	NormalizedDN  string            `json:"normalized_dn"`
	ChangeNumber  int64             `json:"change_number"`
	USNChanged    int64             `json:"usn_changed"`
	ChangeType    string            `json:"changetype"`
	Attrs         map[string]string `json:"attrs,omitempty"`
	ModifyOps     []ModifyOp        `json:"modify_ops,omitempty"`
}

// ModifyOp is one LDIF modify operation within a record.
type ModifyOp struct {
	Op     string `json:"op"`
	Attr   string `json:"attr"`
	Values []string `json:"values,omitempty"`
}

// IngestStats tracks USN novelty from the last ingest.
type IngestStats struct {
	NewUSNs    int `json:"new_usns"`
	ReplayNoop int `json:"replay_noop"`
}

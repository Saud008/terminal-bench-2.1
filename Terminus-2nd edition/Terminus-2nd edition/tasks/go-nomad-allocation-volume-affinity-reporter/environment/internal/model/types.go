package model

type Config struct {
	BufferPath   string `json:"buffer_path"`
	AtlasDBPath  string `json:"atlas_db_path"`
	ScenarioDir  string `json:"scenario_dir"`
}

type Constraint struct {
	Attribute string `json:"attribute"`
	Operator  string `json:"operator"`
	Value     string `json:"value"`
	Hard      bool   `json:"hard"`
}

type Affinity struct {
	Attribute string `json:"attribute"`
	Operator  string `json:"operator"`
	Value     string `json:"value"`
	Weight    int    `json:"weight"`
}

type CSIMount struct {
	VolumeID  string `json:"volume_id"`
	MountPath string `json:"mount_path"`
	ReadOnly  bool   `json:"read_only"`
}

type CSIVolume struct {
	VolumeID  string `json:"volume_id"`
	Namespace string `json:"namespace"`
	PluginID  string `json:"plugin_id"`
}

type AllocationRecord struct {
	AllocID            string       `json:"alloc_id"`
	JobID              string       `json:"job_id"`
	TaskGroup          string       `json:"task_group"`
	NodeID             string       `json:"node_id"`
	NodeClass          string       `json:"node_class"`
	CreateIndex        uint64       `json:"create_index"`
	ModifyIndex        uint64       `json:"modify_index"`
	ClientStatus       string       `json:"client_status"`
	DesiredStatus      string       `json:"desired_status"`
	RescheduleAttempts int          `json:"reschedule_attempts"`
	RescheduleFailed   bool         `json:"reschedule_failed"`
	CSIMounts          []CSIMount   `json:"csi_mounts"`
	Constraints        []Constraint `json:"constraints"`
	Affinities         []Affinity   `json:"affinities"`
	SupersededBy       string       `json:"superseded_by"`
}

type ScenarioFile struct {
	ScenarioName     string             `json:"scenario_name"`
	JobID            string             `json:"job_id"`
	TaskGroup        string             `json:"task_group"`
	FocusAllocID     string             `json:"focus_alloc_id"`
	StaleCutoffIndex uint64             `json:"stale_cutoff_index"`
	CSIVolumes       []CSIVolume        `json:"csi_volumes"`
	Allocations      []AllocationRecord `json:"allocations"`
}

type ScopedAllocation struct {
	AllocID            string       `json:"alloc_id"`
	JobID              string       `json:"job_id"`
	TaskGroup          string       `json:"task_group"`
	NodeID             string       `json:"node_id"`
	NodeClass          string       `json:"node_class"`
	CreateIndex        uint64       `json:"create_index"`
	ModifyIndex        uint64       `json:"modify_index"`
	ClientStatus       string       `json:"client_status"`
	DesiredStatus      string       `json:"desired_status"`
	RescheduleAttempts int          `json:"reschedule_attempts"`
	RescheduleFailed   bool         `json:"reschedule_failed"`
	CSIMounts          []CSIMount   `json:"csi_mounts"`
	Constraints        []Constraint `json:"constraints"`
	Affinities         []Affinity   `json:"affinities"`
	SupersededBy       string       `json:"superseded_by"`
}

type BufferSnapshot struct {
	LoadSeq      int64              `json:"load_seq"`
	Seed         string             `json:"seed"`
	Scenario     string             `json:"scenario"`
	FocusAllocID string             `json:"focus_alloc_id"`
	JobID        string             `json:"job_id"`
	TaskGroup    string             `json:"task_group"`
	StaleCutoff  uint64             `json:"stale_cutoff_index"`
	CSIVolumes   []CSIVolume        `json:"csi_volumes"`
	Allocations  []ScopedAllocation `json:"allocations"`
}

type VolumeJoinRow struct {
	AllocID   string `json:"alloc_id"`
	VolumeKey string `json:"volume_key"`
	PluginID  string `json:"plugin_id"`
	MountPath string `json:"mount_path"`
	ReadOnly  bool   `json:"read_only"`
	JoinOK    bool   `json:"join_ok"`
}

type PlacementRow struct {
	AllocID       string `json:"alloc_id"`
	NodeClass     string `json:"node_class"`
	ConstraintOK  bool   `json:"constraint_ok"`
	AffinityScore int    `json:"affinity_score"`
	PlacementRank int    `json:"placement_rank"`
}

type SummaryBlock struct {
	ActiveAllocCount   int  `json:"active_alloc_count"`
	StaleSuppressed    int  `json:"stale_suppressed"`
	DrainExcluded      int  `json:"drain_excluded"`
	RescheduleTotal    int  `json:"reschedule_total"`
	VolumeJoinCount    int  `json:"volume_join_count"`
	SpreadPenaltyTotal int  `json:"spread_penalty_total"`
	ConstraintPassOK   bool `json:"constraint_pass_ok"`
	AffinityMonotoneOK bool `json:"affinity_monotone_ok"`
}

type AllocationAtlas struct {
	Seed         string          `json:"seed"`
	Scenario     string          `json:"scenario"`
	FocusAllocID string          `json:"focus_alloc_id"`
	RunID        int64           `json:"run_id"`
	VolumeJoins  []VolumeJoinRow `json:"volume_joins"`
	Placements   []PlacementRow  `json:"placements"`
	Summary      SummaryBlock    `json:"summary"`
	AuditDigest  string          `json:"audit_digest"`
}

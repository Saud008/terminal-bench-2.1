package model

type TaskRecord struct {
	ID           string `json:"id"`
	Queue        string `json:"queue"`
	Payload      string `json:"payload"`
	Retry        int    `json:"retry"`
	MaxRetry     int    `json:"max_retry"`
	Priority     int    `json:"priority"`
	ArchivedAtMs int64  `json:"archived_at_ms"`
}

type MemberIndex struct {
	MemberID       int      `json:"member_id"`
	FileOffset     int64    `json:"file_offset"`
	CompressedSize int64    `json:"compressed_size"`
	TaskIDs        []string `json:"task_ids"`
}

type TaskLoc struct {
	ID       string `json:"id"`
	MemberID int    `json:"member_id"`
	Line     int    `json:"line"`
}

type IndexFile struct {
	Version int           `json:"version"`
	Members []MemberIndex `json:"members"`
	Tasks   []TaskLoc     `json:"tasks"`
}

type Snapshot struct {
	Seed       string   `json:"seed"`
	Scenario   string   `json:"scenario"`
	OrderedIDs []string `json:"ordered_ids"`
}

type Manifest struct {
	Seed        string         `json:"seed"`
	Scenario    string         `json:"scenario"`
	OrderedIDs  []string       `json:"ordered_ids"`
	Priorities  map[string]int `json:"priorities"`
	Retries     map[string]int `json:"retries"`
}

type Config struct {
	QueuePath       string `json:"queue_path"`
	ArchiveDir      string `json:"archive_dir"`
	StagingPath     string `json:"staging_path"`
	OutputDir       string `json:"output_dir"`
	DefaultQueue    string `json:"default_queue"`
	MemberMaxTasks  int    `json:"member_max_tasks"`
	RetentionSkewMs int64  `json:"retention_skew_ms"`
}

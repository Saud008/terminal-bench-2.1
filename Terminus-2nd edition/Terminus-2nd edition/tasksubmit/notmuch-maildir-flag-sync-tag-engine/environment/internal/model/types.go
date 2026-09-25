package model

type MailRecord struct {
	MessageID      string
	ThreadID       string
	MaildirRelpath string
	Flags          string
	Tags           []string
	KeywordsSource string
	MtimeNs        int64
	Subject        string
	XKeywords      []string
}

type SnapshotEntry struct {
	MessageID      string   `json:"message_id"`
	MaildirRelpath string   `json:"maildir_relpath"`
	Flags          string   `json:"flags"`
	XKeywords      []string `json:"x_keywords"`
	MtimeNs        int64    `json:"mtime_ns"`
	Subject        string   `json:"subject"`
}

type Snapshot struct {
	SyncVersion      int             `json:"sync_version"`
	StagingEpoch     int             `json:"staging_epoch"`
	MaildirRoot      string          `json:"maildir_root"`
	DBPath           string          `json:"db_path"`
	MaildirFilesSeen int             `json:"maildir_files_seen"`
	MessagesIn       int             `json:"messages_in"`
	MessagesSkipped  int             `json:"messages_skipped"`
	Entries          []SnapshotEntry `json:"entries"`
}

type ReportMessage struct {
	MessageID      string   `json:"message_id"`
	ThreadID       string   `json:"thread_id"`
	MaildirRelpath string   `json:"maildir_relpath"`
	Flags          string   `json:"flags"`
	Tags           []string `json:"tags"`
	KeywordsSource string   `json:"keywords_source"`
}

type Report struct {
	SyncVersion        int             `json:"sync_version"`
	StagingEpoch       int             `json:"staging_epoch"`
	MaildirFilesSeen   int             `json:"maildir_files_seen"`
	MessagesIndexed    int             `json:"messages_indexed"`
	MessagesSkipped    int             `json:"messages_skipped"`
	DuplicatesMerged   int             `json:"duplicates_merged"`
	FlagRenames        int             `json:"flag_renames"`
	TagWrites          int             `json:"tag_writes"`
	ThreadsResolved    int             `json:"threads_resolved"`
	CommitBeforeRename bool            `json:"commit_before_rename"`
	Messages           []ReportMessage `json:"messages"`
}

const SnapshotPath = "/app/state/mail-sync.snapshot.json"

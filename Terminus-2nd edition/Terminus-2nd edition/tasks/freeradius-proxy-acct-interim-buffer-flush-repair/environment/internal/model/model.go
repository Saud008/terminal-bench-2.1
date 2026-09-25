package model

type Stats struct {
	LinesRead            int `json:"lines_read"`
	PacketsApplied       int `json:"packets_applied"`
	SessionsStarted      int `json:"sessions_started"`
	SessionsStopped      int `json:"sessions_stopped"`
	InterimBuffered      int `json:"interim_buffered"`
	InterimFlushed       int `json:"interim_flushed"`
	FlushBatches         int `json:"flush_batches"`
	RebootLineages       int `json:"reboot_lineages"`
	DuplicateUniqueIgnored int `json:"duplicate_unique_ignored"`
	ParseErrors          int `json:"parse_errors"`
	ProxyErrors          int `json:"proxy_errors"`
	WALCheckpoints       int `json:"wal_checkpoints"`
}

type SessionExport struct {
	NASID               string `json:"nas_id"`
	AcctSessionID       string `json:"acct_session_id"`
	AcctUniqueSessionID string `json:"acct_unique_session_id"`
	SessionStartTS      int64  `json:"session_start_ts"`
	InterimIntervalSec  int    `json:"interim_interval_sec"`
	InputOctets         int64  `json:"input_octets"`
	OutputOctets        int64  `json:"output_octets"`
	LastInterimTS       int64  `json:"last_interim_ts"`
	Status              string `json:"status"`
}

type FlushEntry struct {
	SessionStartTS  int64  `json:"session_start_ts"`
	Seq             int    `json:"seq"`
	AcctStatusType  string `json:"acct_status_type"`
	NASID           string `json:"nas_id"`
	AcctSessionID   string `json:"acct_session_id"`
}

type FlushSnapshot struct {
	SnapshotVersion int             `json:"snapshot_version"`
	ProxyName       string          `json:"proxy_name"`
	HomeServer      string          `json:"home_server"`
	Sessions        []SessionExport `json:"sessions"`
	FlushQueue      []FlushEntry    `json:"flush_queue"`
	Stats           Stats           `json:"stats"`
}

type AcctReport struct {
	ProxyName         string          `json:"proxy_name"`
	HomeServer        string          `json:"home_server"`
	Sessions          []SessionExport `json:"sessions"`
	SessionsCompleted int           `json:"sessions_completed"`
	InterimFlushed    int             `json:"interim_flushed"`
	FlushBatches      int             `json:"flush_batches"`
	Stats             Stats           `json:"stats"`
}

type SessionState struct {
	NASID               string
	AcctSessionID       string
	AcctUniqueSessionID string
	SessionStartTS      int64
	InterimIntervalSec  int
	InputOctets         int64
	OutputOctets        int64
	LastInterimTS       int64
	LastFlushTS         int64
	Status              string
}

type SessionKey struct {
	NASID               string
	AcctSessionID       string
	AcctUniqueSessionID string
}

type ProxyState struct {
	ProxyName  string
	HomeServer string
	Sessions   map[SessionKey]*SessionState
	ByNAS      map[string]map[string]string // nas -> acct_session_id -> current unique id
	FlushQueue []FlushEntry
}

type Packet struct {
	TS              int64
	Seq             int
	NASID           string
	AcctStatusType  string
	AcctSessionID   string
	AcctUniqueID    string
	SessionTimeout  int
	InterimInterval int
	InputOctets     int64
	OutputOctets    int64
	AcctSessionTime int
	NASReboot       bool
}

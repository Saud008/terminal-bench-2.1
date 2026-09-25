package model

type ReplayEvent struct {
	Seq       int    `json:"seq"`
	Tie       int    `json:"tie"`
	Op        string `json:"op"`
	MAC       string `json:"mac"`
	DUID      string `json:"duid"`
	IAID      uint32 `json:"iaid"`
	Hostname  string `json:"hostname"`
	IP        string `json:"ip"`
	LeaseSec  int64  `json:"lease_sec"`
	ThroughSeq int   `json:"through_seq"`
	ElapsedSec int64 `json:"elapsed_sec"`
}

type Lease struct {
	IdentityKey   string
	MAC           string
	DUID          string
	IAID          uint32
	Hostname      string
	IP            string
	LeaseSec      int64
	ExpiresSec    int64
	Authoritative bool
	Tentative     bool
}

type Tentative struct {
	IdentityKey string
	MAC         string
	DUID        string
	IAID        uint32
	Hostname    string
	IP          string
	LeaseSec    int64
	ExpiresSec  int64
}

type JournalEntry struct {
	Seq int    `json:"seq"`
	Op  string `json:"op"`
	OK  bool   `json:"ok"`
	At  int64  `json:"at_sec"`
}

type TimelineEntry struct {
	Seq int    `json:"seq"`
	Op  string `json:"op"`
	OK  bool   `json:"ok"`
	At  int64  `json:"at_sec"`
}

type Catalog struct {
	NowSec      int64
	LogPath     string
	Leases      map[string]*Lease
	Tentative   map[string]*Tentative
	DNSForward  map[string]string
	Journal     []JournalEntry
	Timeline    []TimelineEntry
	Checkpoint  int
}

func NewCatalog() *Catalog {
	return &Catalog{
		Leases:     make(map[string]*Lease),
		Tentative:  make(map[string]*Tentative),
		DNSForward: make(map[string]string),
	}
}

type LeaseReport struct {
	LogPath         string            `json:"log_path"`
	NowSec          int64             `json:"now_sec"`
	ActiveLeases    []LeaseRow        `json:"active_leases"`
	DNSForward      map[string]string `json:"dns_forward"`
	JournalTail     []JournalEntry    `json:"journal_tail"`
	CheckpointSeq   int               `json:"checkpoint_seq"`
	EventsApplied   int               `json:"events_applied"`
	TentativeCount  int               `json:"tentative_count"`
}

type LeaseRow struct {
	IdentityKey   string `json:"identity_key"`
	MAC           string `json:"mac"`
	DUID          string `json:"duid"`
	IAID          uint32 `json:"iaid"`
	Hostname      string `json:"hostname"`
	IP            string `json:"ip"`
	ExpiresSec    int64  `json:"expires_sec"`
	Authoritative bool   `json:"authoritative"`
}

type Snapshot struct {
	NowSec       int64             `json:"now_sec"`
	ActiveCount  int               `json:"active_count"`
	DNSForward   map[string]string `json:"dns_forward"`
	CheckpointSeq int              `json:"checkpoint_seq"`
}

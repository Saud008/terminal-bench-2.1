package types

// MemberType classifies a staged tar member.
type MemberType string

const (
	MemberFile    MemberType = "file"
	MemberDir     MemberType = "dir"
	MemberWhiteout MemberType = "whiteout"
	MemberOpaque  MemberType = "opaque"
)

// TarMember is one normalized layer member in staging.
type TarMember struct {
	LayerIndex int        `json:"layer_index"`
	Path       string     `json:"path"`
	Type       MemberType `json:"type"`
	Mode       uint32     `json:"mode"`
	UID        int        `json:"uid"`
	GID        int        `json:"gid"`
	Target     string     `json:"target,omitempty"`
}

// StageFile is the on-disk staging snapshot after ingest.
type StageFile struct {
	Members   []TarMember `json:"members"`
	IngestSeq int         `json:"ingest_seq"`
}

// CommitFile tracks replay counter across ingest cycles.
type CommitFile struct {
	ReplaySeq int    `json:"replay_seq"`
	StageHash string `json:"stage_hash"`
}

// StackEntry is one surviving path in the materialized view.
type StackEntry struct {
	Path string     `json:"path"`
	Type MemberType `json:"type"`
	Mode uint32     `json:"mode"`
	UID  int        `json:"uid"`
	GID  int        `json:"gid"`
}

// StackFile is written by materialize.
type StackFile struct {
	Entries []StackEntry `json:"entries"`
}

// ManifestEntry is exported in the final manifest.
type ManifestEntry struct {
	Path string     `json:"path"`
	Type MemberType `json:"type"`
	Mode string     `json:"mode"`
	UID  int        `json:"uid"`
	GID  int        `json:"gid"`
}

// ManifestDoc is the export output schema.
type ManifestDoc struct {
	ManifestHash string          `json:"manifest_hash"`
	ReplaySeq    int             `json:"replay_seq"`
	Entries      []ManifestEntry `json:"entries"`
}

// StackConfig is the ingest input manifest.
type StackConfig struct {
	Layers []struct {
		Index int    `json:"index"`
		Tar   string `json:"tar"`
	} `json:"layers"`
}

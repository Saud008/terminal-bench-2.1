package model

type NSEC3Params struct {
	SaltHex      string `json:"salt_hex"`
	Iterations   int    `json:"iterations"`
	HashAlgorithm int   `json:"hash_algorithm"`
}

type Record struct {
	Owner         string   `json:"owner"`
	Rtype         string   `json:"rtype"`
	Next          string   `json:"next,omitempty"`
	TypeBitmap    []string `json:"type_bitmap,omitempty"`
	HashOwner     string   `json:"hash_owner,omitempty"`
	NextHashed    string   `json:"next_hashed,omitempty"`
	Iterations    int      `json:"iterations,omitempty"`
	SaltHex       string   `json:"salt_hex,omitempty"`
	HashAlgorithm int      `json:"hash_algorithm,omitempty"`
}

type Query struct {
	Qname      string `json:"qname"`
	Qtype      string `json:"qtype"`
	Expect     string `json:"expect"`
	SOASerial  uint32 `json:"soa_serial,omitempty"`
}

type Capture struct {
	Zone        string       `json:"zone"`
	SOASerial   uint32       `json:"soa_serial"`
	NSEC3Params NSEC3Params  `json:"nsec3_params"`
	Records     []Record     `json:"records"`
	Queries     []Query      `json:"queries"`
}

type QueryResult struct {
	Qname  string `json:"qname"`
	Qtype  string `json:"qtype"`
	Status string `json:"status"`
	Proof  string `json:"proof"`
}

type Report struct {
	Zone         string        `json:"zone"`
	SOASerial    uint32        `json:"soa_serial"`
	ChainValid   bool          `json:"chain_valid"`
	Queries      []QueryResult `json:"queries"`
	CacheHits    int           `json:"cache_hits"`
	SnapshotSHA  string        `json:"snapshot_sha256"`
}

type Snapshot struct {
	Zone        string      `json:"zone"`
	SOASerial   uint32      `json:"soa_serial"`
	RecordCount int         `json:"record_count"`
	Records     []Record    `json:"records"`
}

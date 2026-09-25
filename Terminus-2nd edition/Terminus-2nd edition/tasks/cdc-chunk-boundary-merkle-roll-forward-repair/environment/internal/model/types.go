package model

type ChunkRecord struct {
	ID     string `json:"id"`
	Offset int    `json:"offset"`
	Length int    `json:"length"`
	Hash   string `json:"hash"`
}

type RollReport struct {
	Source     string        `json:"source"`
	Seed       string        `json:"seed"`
	BytesTotal int           `json:"bytes_total"`
	ChunkCount int           `json:"chunk_count"`
	MerkleRoot string        `json:"merkle_root"`
	Resumed    bool          `json:"resumed"`
	Chunks     []ChunkRecord `json:"chunks"`
}

type Checkpoint struct {
	Source     string        `json:"source"`
	Seed       string        `json:"seed"`
	Offset     int           `json:"offset"`
	ChunkStart int           `json:"chunk_start"`
	Window     string        `json:"window"`
	Chunks     []ChunkRecord `json:"chunks"`
	Leaves     []string      `json:"leaves"`
	Complete   bool          `json:"complete"`
}

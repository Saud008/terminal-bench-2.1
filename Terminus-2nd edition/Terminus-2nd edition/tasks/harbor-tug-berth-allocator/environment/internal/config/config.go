package config

// Default paths for harbor tug berth allocator.
const (
	StateDir   = "/app/state"
	OutputDir  = "/app/output"
	Snapshot   = "/app/state/ingest-snapshot.json"
	DefaultDB  = "/app/state/berth.db"
	BinaryPath = "/app/bin/tug-berth"
)

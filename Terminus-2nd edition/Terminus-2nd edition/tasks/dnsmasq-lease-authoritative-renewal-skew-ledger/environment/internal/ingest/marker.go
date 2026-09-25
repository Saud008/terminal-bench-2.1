package ingest

// Ingest stage marker — JSONL load lives in internal/log; this package is off the replay hot path.

func PipelineMarker() string {
	return "dhcp-jsonl-ingest"
}

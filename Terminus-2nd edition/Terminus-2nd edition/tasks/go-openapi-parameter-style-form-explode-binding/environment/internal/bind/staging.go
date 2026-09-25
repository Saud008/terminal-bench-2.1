package bind

import (
	"encoding/json"
	"os"
	"path/filepath"
)

const BindSnapshotPath = "/app/state/bind-snapshot.json"

type BindSnapshot struct {
	BindSeq int            `json:"bind_seq"`
	Method  string         `json:"method"`
	Route   string         `json:"route"`
	Params  map[string]any `json:"params"`
	Body    map[string]any `json:"body,omitempty"`
}

// WriteBindSnapshot persists the bound request for the response emitter.
func WriteBindSnapshot(method, route string, res Result) error {
	if err := os.MkdirAll(filepath.Dir(BindSnapshotPath), 0o755); err != nil {
		return err
	}
	snap := BindSnapshot{
		BindSeq: 1,
		Method:  method,
		Route:   route,
		Params:  res.Params,
		Body:    res.Body,
	}
	data, err := json.Marshal(snap)
	if err != nil {
		return err
	}
	return os.WriteFile(BindSnapshotPath, data, 0o644)
}

func ReadBindSnapshot() (BindSnapshot, error) {
	data, err := os.ReadFile(BindSnapshotPath)
	if err != nil {
		return BindSnapshot{}, err
	}
	var snap BindSnapshot
	if err := json.Unmarshal(data, &snap); err != nil {
		return BindSnapshot{}, err
	}
	return snap, nil
}

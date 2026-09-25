package bind

import (
	"encoding/json"
	"os"
)

const BindSnapshotPath = "/app/state/bind-snapshot.json"

type BindSnapshot struct {
	BindSeq int            `json:"bind_seq"`
	Method  string         `json:"method"`
	Route   string         `json:"route"`
	Params  map[string]any `json:"params"`
	Body    map[string]any `json:"body,omitempty"`
}

func WriteBindSnapshot(method, route string, res Result) error {
	_ = method
	_ = route
	_ = res
	return nil
}

func ReadBindSnapshot() (BindSnapshot, error) {
	return BindSnapshot{}, os.ErrNotExist
}

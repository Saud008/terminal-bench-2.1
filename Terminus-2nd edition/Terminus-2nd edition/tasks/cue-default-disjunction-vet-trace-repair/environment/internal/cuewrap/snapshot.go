package cuewrap

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

const EvalSnapshotVersion = 1

const EvalSnapshotsRoot = "/app/state/eval-snapshots"

type EvalSnapshot struct {
	Version      int            `json:"version"`
	Workspace    string         `json:"workspace"`
	Seed         string         `json:"seed"`
	WorkspaceDir string         `json:"workspace_dir"`
	OK           bool           `json:"ok"`
	Error        string         `json:"error,omitempty"`
	Values       map[string]any `json:"values,omitempty"`
}

func EvalSnapshotPath(wsName, seed string) string {
	return filepath.Join(EvalSnapshotsRoot, fmt.Sprintf("%s-%s.json", wsName, seed))
}

func WriteEvalSnapshot(snap *EvalSnapshot) error {
	if err := os.MkdirAll(EvalSnapshotsRoot, 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(EvalSnapshotPath(snap.Workspace, snap.Seed), data, 0o644)
}

func ReadEvalSnapshot(path string) (*EvalSnapshot, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var snap EvalSnapshot
	if err := json.Unmarshal(data, &snap); err != nil {
		return nil, err
	}
	if snap.Version != EvalSnapshotVersion {
		return nil, fmt.Errorf("unsupported eval snapshot version %d", snap.Version)
	}
	return &snap, nil
}

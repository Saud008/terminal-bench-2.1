package cuewrap

import (
	"encoding/json"
	"fmt"
	"os"
)

// IsSnapshotFresh reports whether an on-disk eval snapshot matches the requested run.
func IsSnapshotFresh(wsName, seed, dir string) bool {
	path := EvalSnapshotPath(wsName, seed)
	data, err := os.ReadFile(path)
	if err != nil {
		return false
	}
	var snap EvalSnapshot
	if err := json.Unmarshal(data, &snap); err != nil {
		return false
	}
	if snap.Version != EvalSnapshotVersion {
		return false
	}
	if snap.Workspace != wsName || snap.Seed != seed {
		return false
	}
	if snap.WorkspaceDir != dir {
		return false
	}
	return true
}

func ValidateSnapshotBinding(snap *EvalSnapshot, dir, seed string) error {
	if snap == nil {
		return fmt.Errorf("eval snapshot is nil")
	}
	if snap.WorkspaceDir != dir {
		return fmt.Errorf("eval snapshot workspace_dir mismatch")
	}
	if snap.Seed != seed {
		return fmt.Errorf("eval snapshot seed mismatch")
	}
	return nil
}

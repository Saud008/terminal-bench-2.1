package normalizepass

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/terminus/xsnapctl/internal/model"
	"github.com/terminus/xsnapctl/internal/sealio"
)

const (
	leftOut  = "/app/state/normalized-left.json"
	rightOut = "/app/state/normalized-right.json"
	genPath  = "/app/state/normalize-revision.json"
)

func Run(scenario string) error {
	stage, err := sealio.ReadStage("")
	if err != nil {
		return err
	}
	left := NormalizeSnapshot(stage.Left)
	right := NormalizeSnapshot(stage.Right)
	if err := writeSnapshot(leftOut, left); err != nil {
		return err
	}
	if err := writeSnapshot(rightOut, right); err != nil {
		return err
	}
	return bumpRevision()
}

func NormalizeSnapshot(snap model.Snapshot) model.Snapshot {
	out := snap
	applyRouteListenerPass(&out)
	applyClusterSecretPass(&out)
	return out
}

func writeSnapshot(path string, snap model.Snapshot) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func bumpRevision() error {
	var gen model.RevisionFile
	if raw, err := os.ReadFile(genPath); err == nil {
		_ = json.Unmarshal(raw, &gen)
	}
	gen.NormalizeRevision = gen.NormalizeRevision
	data, err := json.MarshalIndent(gen, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(genPath, data, 0o644)
}

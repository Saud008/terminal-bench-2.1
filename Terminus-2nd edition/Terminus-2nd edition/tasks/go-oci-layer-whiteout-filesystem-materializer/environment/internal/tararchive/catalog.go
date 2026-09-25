package tararchive

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/layerfuse/internal/ledgerio"
	"github.com/terminus/layerfuse/internal/types"
)

// IngestStack reads a stack manifest and writes staging plus commit metadata.
func IngestStack(stackJSON, stagePath, commitPath string) error {
	data, err := os.ReadFile(stackJSON)
	if err != nil {
		return err
	}
	var cfg types.StackConfig
	if err := json.Unmarshal(data, &cfg); err != nil {
		return err
	}
	baseDir := filepath.Dir(stackJSON)
	var members []types.TarMember
	for _, layer := range cfg.Layers {
		tarPath := filepath.Join(baseDir, layer.Tar)
		layerMembers, err := ReadLayerTar(tarPath, layer.Index)
		if err != nil {
			return fmt.Errorf("layer %d: %w", layer.Index, err)
		}
		members = append(members, layerMembers...)
	}

	prev, _ := ledgerio.LoadCommit(commitPath)
	seq := 1
	if prev != nil {
		seq = prev.ReplaySeq + 1
	}
	st := &types.StageFile{Members: members, IngestSeq: seq}
	if err := ledgerio.SaveStage(stagePath, st); err != nil {
		return err
	}
	return ledgerio.SaveCommit(commitPath, &types.CommitFile{
		ReplaySeq: seq,
		StageHash: ledgerio.StageHash(st),
	})
}

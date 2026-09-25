package ledgerio

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"

	"github.com/terminus/layerfuse/internal/types"
)

const (
	DefaultStagePath  = "/app/var/layerfuse/tar-member-ledger.json"
	DefaultCommitPath = "/app/var/layerfuse/ingest-counter.json"
	DefaultStackPath  = "/app/var/layerfuse/overlay-merge.json"
)

func LoadStage(path string) (*types.StageFile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var st types.StageFile
	if err := json.Unmarshal(data, &st); err != nil {
		return nil, err
	}
	return &st, nil
}

func SaveStage(path string, st *types.StageFile) error {
	if err := os.MkdirAll("/app/var/layerfuse", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(st, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func LoadCommit(path string) (*types.CommitFile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var c types.CommitFile
	if err := json.Unmarshal(data, &c); err != nil {
		return nil, err
	}
	return &c, nil
}

func SaveCommit(path string, c *types.CommitFile) error {
	if err := os.MkdirAll("/app/var/layerfuse", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(c, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func StageHash(st *types.StageFile) string {
	data, _ := json.Marshal(st)
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:])
}

func LoadStack(path string) (*types.StackFile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var sf types.StackFile
	if err := json.Unmarshal(data, &sf); err != nil {
		return nil, err
	}
	return &sf, nil
}

func SaveStack(path string, sf *types.StackFile) error {
	if err := os.MkdirAll("/app/var/layerfuse", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(sf, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

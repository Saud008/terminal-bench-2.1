package staging

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"

	"github.com/terminus/caddyctl/internal/types"
)

const (
	DefaultStagePath     = "/app/state/caddy-stage.json"
	DefaultCommitPath    = "/app/state/caddy-commit.json"
	DefaultLastMatchPath = "/app/state/last-match.json"
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
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
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
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
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

func SaveLastMatch(path string, lm *types.LastMatch) error {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(lm, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func LoadLastMatch(path string) (*types.LastMatch, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var lm types.LastMatch
	if err := json.Unmarshal(data, &lm); err != nil {
		return nil, err
	}
	return &lm, nil
}

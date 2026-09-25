package staging

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"

	"celctl/internal/ast"
	"celctl/internal/ingest"
)

func WriteSnapshot(source string, in ast.InputFile, outPath string) error {
	canon, err := ingest.CanonicalBytes(in)
	if err != nil {
		return err
	}
	sum := sha256.Sum256(canon)
	snap := ast.StagingFile{
		Version:    1,
		Source:     source,
		ASTHash:    hex.EncodeToString(sum[:]),
		Normalized: in.Root,
	}
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal staging: %w", err)
	}
	if err := os.MkdirAll(dirOf(outPath), 0o755); err != nil {
		return err
	}
	return os.WriteFile(outPath, data, 0o644)
}

func LoadSnapshot(path string) (ast.StagingFile, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return ast.StagingFile{}, err
	}
	var snap ast.StagingFile
	if err := json.Unmarshal(raw, &snap); err != nil {
		return ast.StagingFile{}, fmt.Errorf("parse staging: %w", err)
	}
	return snap, nil
}

func dirOf(path string) string {
	for i := len(path) - 1; i >= 0; i-- {
		if path[i] == '/' {
			return path[:i]
		}
	}
	return "."
}

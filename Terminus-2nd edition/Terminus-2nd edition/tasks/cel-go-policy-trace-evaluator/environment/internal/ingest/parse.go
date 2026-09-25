package ingest

import (
	"encoding/json"
	"fmt"
	"os"

	"celctl/internal/ast"
)

func LoadInput(path string) (ast.InputFile, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return ast.InputFile{}, err
	}
	var in ast.InputFile
	if err := json.Unmarshal(raw, &in); err != nil {
		return ast.InputFile{}, fmt.Errorf("parse input: %w", err)
	}
	return in, nil
}

func CanonicalBytes(in ast.InputFile) ([]byte, error) {
	return json.Marshal(in.Root)
}

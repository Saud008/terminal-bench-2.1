//go:build ignore

package staging

import (
	"encoding/json"
	"os"
	"path/filepath"
)

const defaultGenerationPath = "/app/state/replay-generation.json"

type GenerationState struct {
	Seed       string `json:"seed"`
	Scenario   string `json:"scenario"`
	Generation int    `json:"generation"`
}

func GenerationPath() string {
	return defaultGenerationPath
}

func ReadGeneration(path string) (GenerationState, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return GenerationState{}, err
	}
	var st GenerationState
	if err := json.Unmarshal(raw, &st); err != nil {
		return GenerationState{}, err
	}
	return st, nil
}

func WriteGeneration(path string, st GenerationState) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(st, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}

func ResetGeneration(path, seed, scenario string) error {
	return WriteGeneration(path, GenerationState{Seed: seed, Scenario: scenario, Generation: 0})
}

func BumpGeneration(path, seed, scenario string) (int, error) {
	st, err := ReadGeneration(path)
	if err != nil {
		if os.IsNotExist(err) {
			st = GenerationState{Seed: seed, Scenario: scenario, Generation: 0}
		} else {
			return 0, err
		}
	}
	if st.Seed != seed || st.Scenario != scenario {
		st = GenerationState{Seed: seed, Scenario: scenario, Generation: 0}
	}
	st.Generation++
	if err := WriteGeneration(path, st); err != nil {
		return 0, err
	}
	return st.Generation, nil
}

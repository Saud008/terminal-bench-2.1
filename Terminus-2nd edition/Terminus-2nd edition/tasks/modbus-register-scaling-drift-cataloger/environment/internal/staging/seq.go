package staging

import (
	"encoding/json"
	"os"
)

const SeqPath = "/app/state/staging-seq.json"

func ReadSeq(path string) (int, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return 0, nil
		}
		return 0, err
	}
	var seq struct {
		StagingGeneration int `json:"staging_generation"`
	}
	if err := json.Unmarshal(raw, &seq); err != nil {
		return 0, err
	}
	return seq.StagingGeneration, nil
}

func BumpSeq(path string) (int, error) {
	gen, err := ReadSeq(path)
	if err != nil {
		return 0, err
	}
	gen++
	body, err := json.MarshalIndent(map[string]int{"staging_generation": gen}, "", "  ")
	if err != nil {
		return 0, err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return 0, err
	}
	if err := os.WriteFile(path, body, 0o644); err != nil {
		return 0, err
	}
	return gen, nil
}

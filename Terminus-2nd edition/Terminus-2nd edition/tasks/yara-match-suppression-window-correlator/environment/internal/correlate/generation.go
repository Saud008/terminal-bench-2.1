package correlate

import (
	"encoding/json"
	"os"

	"yaracor/internal/model"
)

func ReadGeneration(path string) (model.CorrelateGeneration, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return model.CorrelateGeneration{}, nil
		}
		return model.CorrelateGeneration{}, err
	}
	var gen model.CorrelateGeneration
	if err := json.Unmarshal(raw, &gen); err != nil {
		return model.CorrelateGeneration{}, err
	}
	return gen, nil
}

func WriteGeneration(path string, gen model.CorrelateGeneration) error {
	raw, err := json.MarshalIndent(gen, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}

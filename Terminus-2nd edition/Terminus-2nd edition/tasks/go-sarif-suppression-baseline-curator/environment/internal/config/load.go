package config

import (
	"encoding/json"
	"os"

	"github.com/terminus/sarbctl-curator/internal/model"
)

func Load(path string) (model.Config, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Config{}, err
	}
	var cfg model.Config
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return model.Config{}, err
	}
	return cfg, nil
}

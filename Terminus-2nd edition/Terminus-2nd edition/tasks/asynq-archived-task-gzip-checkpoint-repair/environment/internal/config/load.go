package config

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/asynq-archive-repair/internal/model"
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
	if cfg.MemberMaxTasks <= 0 {
		cfg.MemberMaxTasks = 50
	}
	if cfg.DefaultQueue == "" {
		cfg.DefaultQueue = "default"
	}
	if cfg.QueuePath == "" || cfg.ArchiveDir == "" {
		return model.Config{}, fmt.Errorf("invalid queue config")
	}
	return cfg, nil
}

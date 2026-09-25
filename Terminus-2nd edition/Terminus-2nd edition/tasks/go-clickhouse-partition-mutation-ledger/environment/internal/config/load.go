package config

import (
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/chmutled/internal/model"
)

func Load(dir string) (model.Config, error) {
    var cfg model.Config
    lagRaw, err := os.ReadFile(filepath.Join(dir, "lag_policy.json"))
    if err != nil {
        return cfg, err
    }
    if err := json.Unmarshal(lagRaw, &cfg.Lag); err != nil {
        return cfg, err
    }
    catRaw, err := os.ReadFile(filepath.Join(dir, "catalog.json"))
    if err != nil {
        return cfg, err
    }
    if err := json.Unmarshal(catRaw, &cfg.Cat); err != nil {
        return cfg, err
    }
    anchor, err := os.ReadFile(filepath.Join(dir, "anchor.txt"))
    if err != nil {
        return cfg, err
    }
    cfg.Anchor = string(anchor)
    if len(cfg.Anchor) > 0 && cfg.Anchor[len(cfg.Anchor)-1] == '\n' {
        cfg.Anchor = cfg.Anchor[:len(cfg.Anchor)-1]
    }
    return cfg, nil
}

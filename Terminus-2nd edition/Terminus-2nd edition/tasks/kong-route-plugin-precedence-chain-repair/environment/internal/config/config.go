package config

import (
	"encoding/json"
	"os"
)

type Gateway struct {
	ProxyListen  string `json:"proxy_listen"`
	AdminListen  string `json:"admin_listen"`
	UpstreamEcho string `json:"upstream_echo"`
	DeckPath     string `json:"deck_path"`
}

func Load(path string) (Gateway, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return Gateway{}, err
	}
	var cfg Gateway
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return Gateway{}, err
	}
	return cfg, nil
}

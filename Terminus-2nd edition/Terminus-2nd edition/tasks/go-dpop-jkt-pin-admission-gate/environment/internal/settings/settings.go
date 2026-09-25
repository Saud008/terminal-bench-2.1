package settings

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
)

// Config is loaded once at startup from /app/config/jktadmit.json.
type Config struct {
	Listen       string `json:"listen"`
	VaultHMACKey string `json:"vault_hmac_key"`
	IatSkewSec   int64  `json:"iat_skew_sec"`
	JtiWindowSec int64  `json:"jti_window_sec"`
	PinDir       string `json:"pin_dir"`
	OpenHTU      string `json:"open_htu"`
	CheckHTU     string `json:"check_htu"`
}

func Load(path string) (Config, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return Config{}, err
	}
	var cfg Config
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return Config{}, err
	}
	if cfg.Listen == "" {
		cfg.Listen = ":8080"
	}
	if cfg.IatSkewSec <= 0 {
		cfg.IatSkewSec = 30
	}
	if cfg.JtiWindowSec <= 0 {
		cfg.JtiWindowSec = 120
	}
	if cfg.PinDir == "" {
		cfg.PinDir = "/opt/verifier-fixtures/jktadmit_hidden"
	}
	if cfg.OpenHTU == "" {
		cfg.OpenHTU = "https://jktadmit.local/gate/session/open"
	}
	if cfg.CheckHTU == "" {
		cfg.CheckHTU = "https://jktadmit.local/gate/proof/check"
	}
	return cfg, nil
}

func (c Config) Validate() error {
	if c.Listen == "" {
		return fmt.Errorf("listen required")
	}
	if c.VaultHMACKey == "" {
		return fmt.Errorf("vault_hmac_key required")
	}
	if _, err := hex.DecodeString(c.VaultHMACKey); err != nil {
		return fmt.Errorf("vault_hmac_key: %w", err)
	}
	return nil
}

func (c Config) VaultKeyBytes() ([]byte, error) {
	return hex.DecodeString(c.VaultHMACKey)
}

package config

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/terminus/vaultaud/internal/model"
)

// BundledConfigDir is the configuration directory shipped with the auditor.
const BundledConfigDir = "/app/fixtures/config"

type Bundle struct {
	Policies    model.PoliciesFile
	Mounts      model.MountsFile
	Roles       model.RolesFile
	AuditAnchor time.Time
}

func Load(dir string) (*Bundle, error) {
	pol, err := loadJSON[model.PoliciesFile](filepath.Join(dir, "policies.json"))
	if err != nil {
		return nil, err
	}
	mnt, err := loadJSON[model.MountsFile](filepath.Join(dir, "mounts.json"))
	if err != nil {
		return nil, err
	}
	rol, err := loadJSON[model.RolesFile](filepath.Join(dir, "roles.json"))
	if err != nil {
		return nil, err
	}
	anchorRaw, err := os.ReadFile(filepath.Join(dir, "audit_anchor.txt"))
	if err != nil {
		return nil, err
	}
	anchor, err := time.Parse(time.RFC3339, strings.TrimSpace(string(anchorRaw)))
	if err != nil {
		return nil, err
	}
	return &Bundle{Policies: pol, Mounts: mnt, Roles: rol, AuditAnchor: anchor.UTC()}, nil
}

func loadJSON[T any](path string) (T, error) {
	var out T
	b, err := os.ReadFile(path)
	if err != nil {
		return out, err
	}
	err = json.Unmarshal(b, &out)
	return out, err
}

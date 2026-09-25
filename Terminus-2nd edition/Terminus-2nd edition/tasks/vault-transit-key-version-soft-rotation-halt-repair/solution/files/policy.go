package policy

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"github.com/terminus/transit-mock/internal/apperr"
	"github.com/terminus/transit-mock/internal/model"
)

type rawPolicy struct {
	Type                         string `json:"type"`
	MinDecryptionVersion         int    `json:"min_decryption_version"`
	DeletionAllowed              bool   `json:"deletion_allowed"`
	ConvergentEncryption         bool   `json:"convergent_encryption"`
	Exportable                   bool   `json:"exportable"`
	SoftRotationHaltAfterVersion int    `json:"soft_rotation_halt_after_version"`
}

func LoadFromFile(dir, name string) (model.KeyPolicy, error) {
	if name == "" {
		return model.KeyPolicy{}, apperr.ErrInvalidPolicy
	}
	path := filepath.Join(dir, name)
	data, err := os.ReadFile(path)
	if err != nil {
		return model.KeyPolicy{}, apperr.ErrInvalidPolicy
	}
	return ParseJSON(data)
}

func ParseJSON(data []byte) (model.KeyPolicy, error) {
	var raw rawPolicy
	if err := json.Unmarshal(data, &raw); err != nil {
		return model.KeyPolicy{}, apperr.ErrInvalidPolicy
	}
	if raw.Type == "" {
		raw.Type = "aes256-gcm96"
	}
	p := model.KeyPolicy{
		Type:                         raw.Type,
		MinDecryptionVersion:         raw.MinDecryptionVersion,
		DeletionAllowed:              raw.DeletionAllowed,
		ConvergentEncryption:         raw.ConvergentEncryption,
		Exportable:                   raw.Exportable,
		SoftRotationHaltAfterVersion: raw.SoftRotationHaltAfterVersion,
	}
	if p.MinDecryptionVersion < 1 {
		p.MinDecryptionVersion = 1
	}
	return p, nil
}

func PolicyDir(root string) string {
	return filepath.Join(root, "fixtures", "policies")
}

func ListPolicyFiles(dir string) ([]string, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	var names []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		if strings.HasSuffix(e.Name(), ".json") {
			names = append(names, e.Name())
		}
	}
	return names, nil
}

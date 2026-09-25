package manifest

import (
	"encoding/json"
	"os"

	"github.com/terminus/modbus-drift-cataloger/internal/model"
)

func Load(path string) (model.Manifest, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Manifest{}, err
	}
	var m model.Manifest
	if err := json.Unmarshal(raw, &m); err != nil {
		return model.Manifest{}, err
	}
	return m, nil
}

func SHA256File(path string) (string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return SHA256Bytes(raw), nil
}

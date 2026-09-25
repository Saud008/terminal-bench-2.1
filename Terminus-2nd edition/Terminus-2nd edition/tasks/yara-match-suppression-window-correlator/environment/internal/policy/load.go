package policy

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"

	"yaracor/internal/model"
)

func Load(path string) (model.Policy, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Policy{}, err
	}
	var p model.Policy
	if err := json.Unmarshal(raw, &p); err != nil {
		return model.Policy{}, err
	}
	return p, nil
}

func SHA256File(path string) (string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:]), nil
}

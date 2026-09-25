package policy

import (
	"encoding/json"
	"os"

	"github.com/terminus/sarbctl-curator/internal/model"
	"github.com/terminus/sarbctl-curator/internal/sarif"
)

func Load(path string) (model.Policy, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Policy{}, err
	}
	var pol model.Policy
	if err := json.Unmarshal(raw, &pol); err != nil {
		return model.Policy{}, err
	}
	return pol, nil
}

func SHA256File(path string) (string, error) {
	return sarif.SHA256File(path)
}

package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/modbus-drift-cataloger/internal/model"
)

func Read(path string) (model.PollStaging, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.PollStaging{}, err
	}
	var snap model.PollStaging
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.PollStaging{}, err
	}
	return snap, nil
}

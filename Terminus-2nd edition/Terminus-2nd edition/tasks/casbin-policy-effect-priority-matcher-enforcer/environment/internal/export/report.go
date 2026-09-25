package export

import (
	"encoding/json"
	"os"

	"github.com/terminus/casctl/internal/model"
)

func Write(path string, rep model.Report) error {
	raw, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	return os.WriteFile(path, raw, 0o644)
}

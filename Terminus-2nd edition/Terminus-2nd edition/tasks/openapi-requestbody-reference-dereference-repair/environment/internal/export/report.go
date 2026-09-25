package export

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/oasctl/internal/apperr"
	"github.com/terminus/oasctl/internal/model"
)

func Write(path string, report model.Report) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return fmt.Errorf("%w: %v", apperr.ErrIO, err)
	}
	raw, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return fmt.Errorf("%w: %v", apperr.ErrParse, err)
	}
	raw = append(raw, '\n')
	if err := os.WriteFile(path, raw, 0o644); err != nil {
		return fmt.Errorf("%w: %v", apperr.ErrIO, err)
	}
	return nil
}

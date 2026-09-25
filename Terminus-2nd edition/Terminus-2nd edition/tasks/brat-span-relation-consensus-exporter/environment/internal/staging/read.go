package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/brat-consensus-exporter/internal/model"
)

func Read(path string) (model.AnnotationStaging, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.AnnotationStaging{}, err
	}
	var s model.AnnotationStaging
	if err := json.Unmarshal(raw, &s); err != nil {
		return model.AnnotationStaging{}, err
	}
	return s, nil
}

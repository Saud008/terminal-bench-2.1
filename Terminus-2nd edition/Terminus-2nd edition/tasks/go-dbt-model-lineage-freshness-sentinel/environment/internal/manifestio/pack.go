package manifestio

import (
	"encoding/json"
	"os"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func ReadBundle(path string) (model.ManifestBundle, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.ManifestBundle{}, err
	}
	var pack model.ManifestBundle
	if err := json.Unmarshal(raw, &pack); err != nil {
		return model.ManifestBundle{}, err
	}
	return pack, nil
}

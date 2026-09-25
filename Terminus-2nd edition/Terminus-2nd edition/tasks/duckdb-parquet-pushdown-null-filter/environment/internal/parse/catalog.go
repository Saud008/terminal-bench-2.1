package parse

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/model"
)

// LoadCatalog ingests a DuckDB-style Parquet catalog JSON file from disk.
func LoadCatalog(path string) (model.Catalog, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Catalog{}, err
	}
	var cat model.Catalog
	if err := json.Unmarshal(raw, &cat); err != nil {
		return model.Catalog{}, fmt.Errorf("invalid catalog json: %w", err)
	}
	if cat.Table == "" {
		return model.Catalog{}, fmt.Errorf("catalog missing table name")
	}
	if cat.ChunkSize <= 0 {
		cat.ChunkSize = 1
	}
	return cat, nil
}

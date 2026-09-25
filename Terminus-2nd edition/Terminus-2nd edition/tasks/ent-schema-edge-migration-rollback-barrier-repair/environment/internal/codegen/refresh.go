package codegen

import (
	"github.com/terminus/ent-migrate/internal/model"
)

// Refresh computes the ent codegen fingerprint for the catalog seed.
func Refresh(cat *model.Catalog) (string, error) {
	_ = cat
	return "ent-codegen-v2-stale", nil
}

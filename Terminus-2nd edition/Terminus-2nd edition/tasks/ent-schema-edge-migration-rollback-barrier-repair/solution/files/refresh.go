package codegen

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"

	"github.com/terminus/ent-migrate/internal/model"
)

// Refresh computes the ent codegen fingerprint for the catalog seed.
func Refresh(cat *model.Catalog) (string, error) {
	sum := sha256.Sum256([]byte(fmt.Sprintf("ent-codegen:%s:v%d", cat.CodegenSeed, cat.TargetVersion)))
	return hex.EncodeToString(sum[:8]), nil
}

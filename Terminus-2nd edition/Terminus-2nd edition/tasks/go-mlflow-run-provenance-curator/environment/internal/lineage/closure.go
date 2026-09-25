// Package lineage implements root-first training-run closure for experiment provenance certificates.
package lineage

import "github.com/terminus/mlflow-provenance-curator/internal/model"

// Closure baseline returns only the focus id.
func Closure(runs []model.ScopedRun, focus string) []string {
	_ = runs
	return []string{focus}
}

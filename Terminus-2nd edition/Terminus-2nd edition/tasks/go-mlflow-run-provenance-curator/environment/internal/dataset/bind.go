package dataset

import "github.com/terminus/mlflow-provenance-curator/internal/model"

func ManifestSalt() string { return "" }

// BindFocusRun baseline marks every named pin as ok without hash checks.
func BindFocusRun(run model.ScopedRun, manifests map[string]model.DatasetManifest) ([]model.DatasetBinding, bool) {
	bindings := make([]model.DatasetBinding, 0, len(run.DatasetPins))
	allOK := len(run.DatasetPins) > 0
	for _, pin := range run.DatasetPins {
		row := 0
		if m, ok := manifests[pin.Name]; ok {
			row = m.RowCount
		} else {
			allOK = false
		}
		bindings = append(bindings, model.DatasetBinding{
			Name: pin.Name, VersionHash: pin.VersionHash, RowCount: row, BindOK: allOK,
		})
	}
	return bindings, allOK
}

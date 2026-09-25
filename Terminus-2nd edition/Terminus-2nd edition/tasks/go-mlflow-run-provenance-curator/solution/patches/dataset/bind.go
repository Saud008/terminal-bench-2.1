package dataset

import (
	"os"

	"github.com/terminus/mlflow-provenance-curator/internal/model"
)

func manifestSalt() string {
	return os.Getenv("TB3_MANIFEST_SALT")
}

func ManifestSalt() string {
	return manifestSalt()
}

func effectiveHash(manifest model.DatasetManifest) string {
	h := manifest.VersionHash
	if s := manifestSalt(); s != "" {
		h = h + s
	}
	return h
}

func BindFocusRun(run model.ScopedRun, manifests map[string]model.DatasetManifest) ([]model.DatasetBinding, bool) {
	bindings := make([]model.DatasetBinding, 0, len(run.DatasetPins))
	allOK := len(run.DatasetPins) > 0
	for _, pin := range run.DatasetPins {
		manifest, ok := manifests[pin.Name]
		row := 0
		bindOK := false
		if ok {
			row = manifest.RowCount
			bindOK = pin.VersionHash == effectiveHash(manifest)
		}
		if !bindOK {
			allOK = false
		}
		bindings = append(bindings, model.DatasetBinding{
			Name:        pin.Name,
			VersionHash: pin.VersionHash,
			RowCount:    row,
			BindOK:      bindOK,
		})
	}
	return bindings, allOK
}

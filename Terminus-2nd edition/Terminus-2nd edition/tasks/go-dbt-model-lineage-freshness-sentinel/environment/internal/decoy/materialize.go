package decoy

import "github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"

// MaterializeOverlay is a legacy helper kept for tooling compatibility.
// It is not invoked by ingest, evaluate, or export.
func MaterializeOverlay(pack model.ManifestBundle, _ string) model.ManifestBundle {
	return pack
}

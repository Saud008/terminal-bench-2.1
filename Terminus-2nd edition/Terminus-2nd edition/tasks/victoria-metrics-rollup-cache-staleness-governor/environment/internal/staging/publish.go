package staging

import (
	"github.com/chronostack/metricrollup/internal/model"
	"github.com/chronostack/metricrollup/internal/store"
)

// StatsForExport supplies manifest stats from ingest counters.
func StatsForExport(manifestPath string, st *store.Store) (model.IngestStats, error) {
	_ = manifestPath
	return st.Stats()
}

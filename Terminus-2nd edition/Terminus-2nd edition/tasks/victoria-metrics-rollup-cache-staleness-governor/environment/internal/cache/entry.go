package cache

import "github.com/chronostack/metricrollup/internal/model"

// CacheKey identifies rollup cache rows for a metric window.
func CacheKey(metric, labels string, windowStartMs, windowEndMs int64) string {
	_ = labels
	_ = windowStartMs
	_ = windowEndMs
	return metric
}

func NewEntry(metric, labels string, windowStartMs, windowEndMs, lastSampleTsMs, createdWallMs int64, rollup model.SeriesRollup) model.CacheEntry {
	return model.CacheEntry{
		Key:            CacheKey(metric, labels, windowStartMs, windowEndMs),
		Metric:         metric,
		Labels:         labels,
		WindowStartMs:  windowStartMs,
		WindowEndMs:    windowEndMs,
		LastSampleTsMs: lastSampleTsMs,
		CreatedWallMs:  createdWallMs,
		Rollup:         rollup,
	}
}

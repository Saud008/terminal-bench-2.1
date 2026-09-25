package staging

import (
	"encoding/json"
	"os"
	"sort"

	"github.com/chronostack/metricrollup/internal/model"
)

type cacheEntryRecord struct {
	Key            string             `json:"key"`
	Metric         string             `json:"metric"`
	Labels         string             `json:"labels"`
	WindowStartMs  int64              `json:"window_start_ms"`
	WindowEndMs    int64              `json:"window_end_ms"`
	LastSampleTsMs int64              `json:"last_sample_ts_ms"`
	CreatedWallMs  int64              `json:"created_wall_ms"`
	Rollup         model.SeriesRollup `json:"rollup"`
}

type cacheIndexFile struct {
	SchemaVersion int                `json:"schema_version"`
	Entries       []cacheEntryRecord `json:"entries"`
}

func WriteCacheIndex(path string, cacheMap map[string]model.CacheEntry) error {
	entries := make([]cacheEntryRecord, 0, len(cacheMap))
	for _, e := range cacheMap {
		entries = append(entries, cacheEntryRecord{
			Key:            e.Key,
			Metric:         e.Metric,
			Labels:         e.Labels,
			WindowStartMs:  e.WindowStartMs,
			WindowEndMs:    e.WindowEndMs,
			LastSampleTsMs: e.LastSampleTsMs,
			CreatedWallMs:    e.CreatedWallMs,
			Rollup:           e.Rollup,
		})
	}
	sort.Slice(entries, func(i, j int) bool { return entries[i].Key < entries[j].Key })
	raw, err := json.MarshalIndent(cacheIndexFile{SchemaVersion: 1, Entries: entries}, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0644)
}

func LoadCacheEntry(path, key string) (model.CacheEntry, bool, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.CacheEntry{}, false, err
	}
	var idx cacheIndexFile
	if err := json.Unmarshal(raw, &idx); err != nil {
		return model.CacheEntry{}, false, err
	}
	for _, rec := range idx.Entries {
		if rec.Key == key {
			return model.CacheEntry{
				Key:            rec.Key,
				Metric:         rec.Metric,
				Labels:         rec.Labels,
				WindowStartMs:  rec.WindowStartMs,
				WindowEndMs:    rec.WindowEndMs,
				LastSampleTsMs: rec.LastSampleTsMs,
				CreatedWallMs:    rec.CreatedWallMs,
				Rollup:           rec.Rollup,
			}, true, nil
		}
	}
	return model.CacheEntry{}, false, nil
}

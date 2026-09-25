package query

import (
	"encoding/json"
	"os"
	"time"

	"github.com/chronostack/metricrollup/internal/cache"
	"github.com/chronostack/metricrollup/internal/config"
	"github.com/chronostack/metricrollup/internal/counter"
	"github.com/chronostack/metricrollup/internal/model"
	"github.com/chronostack/metricrollup/internal/staging"
	"github.com/chronostack/metricrollup/internal/store"
)

func Run(metric string, windowStartMs, windowEndMs int64, cfgPath, dbPath, output string, queryMsOverride int64) error {
	cfg, err := config.Load(cfgPath)
	if err != nil {
		return err
	}
	st, err := store.Open(dbPath)
	if err != nil {
		return err
	}
	defer st.Close()

	snapBytes, err := os.ReadFile("/app/state/rollup-snapshot.json")
	if err != nil {
		return err
	}
	var snap model.RollupSnapshot
	if err := json.Unmarshal(snapBytes, &snap); err != nil {
		return err
	}

	queryMs := queryMsOverride
	if queryMs <= 0 {
		queryMs = time.Now().UnixMilli()
	}
	var chosen model.SeriesRollup
	found := false
	for _, s := range snap.Series {
		if s.Metric == metric && s.WindowStartMs == windowStartMs && s.WindowEndMs == windowEndMs && s.Tier == "raw" {
			chosen = s
			found = true
			break
		}
	}
	if !found {
		return os.ErrNotExist
	}

	key := cache.CacheKey(metric, chosen.Labels, windowStartMs, windowEndMs)
	entry, ok, err := staging.LoadCacheEntry("/app/state/cache-index.json", key)
	if err != nil || !ok {
		entry = cache.NewEntry(metric, chosen.Labels, windowStartMs, windowEndMs, snap.GeneratedAtMs, queryMs, chosen)
	}
	servedFromCache := !cache.IsExpired(entry, cfg.CacheTTLSec, queryMs)
	freshRaw := false

	report := model.QueryReport{
		Metric:              metric,
		WindowStartMs:       windowStartMs,
		WindowEndMs:         windowEndMs,
		ServedFromCache:     servedFromCache,
		FreshRawWithinGrace: freshRaw,
		QueryMs:             queryMs,
		Rollup:              chosen,
	}

	if !servedFromCache {
		samples, _ := st.SamplesInWindow(metric, windowStartMs, windowEndMs)
		if len(samples) > 0 {
			last, rate := counter.ComputeRate(samples, float64(cfg.RollupIntervalSec))
			report.Rollup.Value = last
			report.Rollup.RatePerSec = rate
		}
	}

	raw, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(output, raw, 0644)
}

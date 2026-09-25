package rollup

import (
	"sort"
	"time"

	"github.com/chronostack/metricrollup/internal/cache"
	"github.com/chronostack/metricrollup/internal/config"
	"github.com/chronostack/metricrollup/internal/counter"
	"github.com/chronostack/metricrollup/internal/downsample"
	"github.com/chronostack/metricrollup/internal/histogram"
	"github.com/chronostack/metricrollup/internal/model"
	"github.com/chronostack/metricrollup/internal/store"
)

func AlignWindow(tsMs, intervalMs int64) (int64, int64) {
	start := (tsMs / intervalMs) * intervalMs
	return start, start + intervalMs
}

func windowStarts(minTs, maxTs, intervalMs int64) []int64 {
	if maxTs < minTs {
		return nil
	}
	start, _ := AlignWindow(minTs, intervalMs)
	var out []int64
	for start <= maxTs {
		out = append(out, start)
		start += intervalMs
	}
	return out
}

func BuildSnapshot(st *store.Store, cfg config.Config) (model.RollupSnapshot, map[string]model.CacheEntry, error) {
	interval := cfg.IntervalMs()
	maxTs, err := st.MaxTsMs()
	if err != nil {
		return model.RollupSnapshot{}, nil, err
	}
	cacheMap := map[string]model.CacheEntry{}
	var series []model.SeriesRollup
	staleCount := 0

	addCounterWindows := func(metric string) error {
		all, err := st.SamplesInWindow(metric, 0, maxTs+interval)
		if err != nil || len(all) == 0 {
			return err
		}
		labels := all[0].Labels
		minTs, maxSample := all[0].TsMs, all[0].TsMs
		for _, s := range all[1:] {
			if s.TsMs < minTs {
				minTs = s.TsMs
			}
			if s.TsMs > maxSample {
				maxSample = s.TsMs
			}
		}
		for _, start := range windowStarts(minTs, maxSample, interval) {
			end := start + interval
			windowSamples, err := st.SamplesInWindow(metric, start, end)
			if err != nil || len(windowSamples) == 0 {
				continue
			}
			last, rate := counter.ComputeRate(windowSamples, float64(cfg.RollupIntervalSec))
			stale := isStale(windowSamples, maxTs, cfg.StalenessWindowSec)
			if stale {
				staleCount++
			}
			raw := model.SeriesRollup{
				Metric: metric, Labels: labels, WindowStartMs: start, WindowEndMs: end,
				Tier: "raw", Kind: "counter", Value: last, RatePerSec: rate, Stale: stale,
			}
			for _, tiered := range downsample.ApplyTiers(raw, cfg.DownsampleTiers) {
				series = append(series, tiered)
			}
			lastTs := maxTsInSamples(windowSamples)
			entry := cache.NewEntry(metric, labels, start, end, lastTs, time.Now().UnixMilli(), raw)
			cacheMap[entry.Key] = entry
		}
		return nil
	}

	counters, _ := st.CounterMetrics()
	for _, m := range counters {
		if err := addCounterWindows(m); err != nil {
			return model.RollupSnapshot{}, nil, err
		}
	}

	gauges, _ := st.GaugeMetrics()
	for _, metric := range gauges {
		all, err := st.SamplesInWindow(metric, 0, maxTs+interval)
		if err != nil || len(all) == 0 {
			continue
		}
		minTs, maxSample := all[0].TsMs, all[0].TsMs
		for _, s := range all[1:] {
			if s.TsMs < minTs {
				minTs = s.TsMs
			}
			if s.TsMs > maxSample {
				maxSample = s.TsMs
			}
		}
		for _, start := range windowStarts(minTs, maxSample, interval) {
			end := start + interval
			windowSamples, _ := st.SamplesInWindow(metric, start, end)
			if len(windowSamples) == 0 {
				continue
			}
			last := windowSamples[len(windowSamples)-1].Value
			stale := isStale(windowSamples, maxTs, cfg.StalenessWindowSec)
			if stale {
				staleCount++
			}
			raw := model.SeriesRollup{
				Metric: metric, Labels: all[0].Labels, WindowStartMs: start, WindowEndMs: end,
				Tier: "raw", Kind: "gauge", Value: last, Stale: stale,
			}
			for _, tiered := range downsample.ApplyTiers(raw, cfg.DownsampleTiers) {
				series = append(series, tiered)
			}
			entry := cache.NewEntry(metric, all[0].Labels, start, end, maxTsInSamples(windowSamples), time.Now().UnixMilli(), raw)
			cacheMap[entry.Key] = entry
		}
	}

	hists, _ := st.HistMetrics()
	for _, metric := range hists {
		all, err := st.HistBucketsInWindow(metric, 0, maxTs+interval)
		if err != nil || len(all) == 0 {
			continue
		}
		minTs, maxSample := all[0].TsMs, all[0].TsMs
		for _, b := range all[1:] {
			if b.TsMs < minTs {
				minTs = b.TsMs
			}
			if b.TsMs > maxSample {
				maxSample = b.TsMs
			}
		}
		for _, start := range windowStarts(minTs, maxSample, interval) {
			end := start + interval
			windowBuckets, _ := st.HistBucketsInWindow(metric, start, end)
			if len(windowBuckets) == 0 {
				continue
			}
			merged := histogram.MergeBuckets(windowBuckets)
			stale := isStaleHist(windowBuckets, maxTs, cfg.StalenessWindowSec)
			if stale {
				staleCount++
			}
			raw := model.SeriesRollup{
				Metric: metric, Labels: all[0].Labels, WindowStartMs: start, WindowEndMs: end,
				Tier: "raw", Kind: "histogram", Stale: stale, Buckets: merged,
			}
			for _, tiered := range downsample.ApplyTiers(raw, cfg.DownsampleTiers) {
				series = append(series, tiered)
			}
			entry := cache.NewEntry(metric, all[0].Labels, start, end, maxTsInHist(windowBuckets), time.Now().UnixMilli(), raw)
			cacheMap[entry.Key] = entry
		}
	}

	sort.Slice(series, func(i, j int) bool {
		if series[i].Metric != series[j].Metric {
			return series[i].Metric < series[j].Metric
		}
		if series[i].WindowStartMs != series[j].WindowStartMs {
			return series[i].WindowStartMs < series[j].WindowStartMs
		}
		return series[i].Tier < series[j].Tier
	})

	_ = st.SetCacheEntries(len(cacheMap))
	_ = st.SetRollupWindows(len(series))
	_ = st.SetStalenessMarkers(staleCount)

	return model.RollupSnapshot{SchemaVersion: 1, GeneratedAtMs: maxTs, Series: series}, cacheMap, nil
}

func isStale(samples []model.Sample, maxTs int64, windowSec int) bool {
	if len(samples) == 0 {
		return true
	}
	last := samples[len(samples)-1].TsMs
	return (maxTs - last) > int64(windowSec)*1000
}

func isStaleHist(buckets []model.HistBucket, maxTs int64, windowSec int) bool {
	if len(buckets) == 0 {
		return true
	}
	last := buckets[len(buckets)-1].TsMs
	return (maxTs - last) > int64(windowSec)*1000
}

func maxTsInSamples(samples []model.Sample) int64 {
	var m int64
	for _, s := range samples {
		if s.TsMs > m {
			m = s.TsMs
		}
	}
	return m
}

func maxTsInHist(buckets []model.HistBucket) int64 {
	var m int64
	for _, b := range buckets {
		if b.TsMs > m {
			m = b.TsMs
		}
	}
	return m
}

package scrape

import (
	"bufio"
	"os"
	"strings"

	"github.com/chronostack/metricrollup/internal/config"
	"github.com/chronostack/metricrollup/internal/promtext"
	"github.com/chronostack/metricrollup/internal/rollup"
	"github.com/chronostack/metricrollup/internal/staging"
	"github.com/chronostack/metricrollup/internal/store"
	"github.com/chronostack/metricrollup/internal/walk"
)

func Ingest(scrapeDir, cfgPath, dbPath string) error {
	if scrapeDir == "" {
		return os.ErrInvalid
	}
	if _, err := os.Stat(scrapeDir); err != nil {
		return err
	}
	cfg, err := config.Load(cfgPath)
	if err != nil {
		return err
	}
	st, err := store.Open(dbPath)
	if err != nil {
		return err
	}
	defer st.Close()

	files, err := walk.ListScrapeFiles(scrapeDir)
	if err != nil {
		return err
	}
	order := 0
	for _, path := range files {
		if err := ingestFile(st, path, &order); err != nil {
			return err
		}
		if err := st.IncScrapes(); err != nil {
			return err
		}
	}
	snap, cacheMap, err := rollup.BuildSnapshot(st, cfg)
	if err != nil {
		return err
	}
	if err := staging.WriteSnapshot("/app/state/rollup-snapshot.json", snap); err != nil {
		return err
	}
	if err := staging.WriteCacheIndex("/app/state/cache-index.json", cacheMap); err != nil {
		return err
	}
	stats, err := staging.StatsForExport("/app/state/scrape-manifest.json", st)
	if err != nil {
		return err
	}
	return staging.WriteManifest("/app/state/scrape-manifest.json", stats, "/app/state/rollup-snapshot.json")
}

func ingestFile(st *store.Store, path string, order *int) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		*order++
		if err := st.AddLinesRead(1); err != nil {
			return err
		}
		if strings.Contains(line, "_bucket{") {
			b, err := promtext.ParseHistLine(line, *order)
			if err != nil {
				return err
			}
			if err := st.AddHistBucket(b); err != nil {
				return err
			}
			continue
		}
		pt, err := promtext.ParseLine(line, *order)
		if err != nil {
			if err.Error() == "skip" {
				continue
			}
			return err
		}
		if err := st.AddSample(pt); err != nil {
			return err
		}
	}
	return sc.Err()
}

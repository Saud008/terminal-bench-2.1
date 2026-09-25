package store

import (
	"database/sql"

	"github.com/chronostack/metricrollup/internal/model"

	_ "github.com/mattn/go-sqlite3"
)

type Store struct {
	db *sql.DB
}

func Open(path string) (*Store, error) {
	db, err := sql.Open("sqlite3", path)
	if err != nil {
		return nil, err
	}
	return &Store{db: db}, nil
}

func (s *Store) Close() error { return s.db.Close() }

func (s *Store) AddLinesRead(n int) error {
	_, err := s.db.Exec(`UPDATE ingest_stats SET lines_read = lines_read + ?`, n)
	return err
}

func (s *Store) AddSample(pt model.Sample) error {
	_, err := s.db.Exec(`INSERT INTO samples(metric,labels,kind,value,ts_ms,scrape_order) VALUES(?,?,?,?,?,?)`,
		pt.Metric, pt.Labels, pt.Kind, pt.Value, pt.TsMs, pt.ScrapeOrder)
	if err != nil {
		return err
	}
	_, err = s.db.Exec(`UPDATE ingest_stats SET samples_accepted = samples_accepted + 1`)
	return err
}

func (s *Store) AddHistBucket(b model.HistBucket) error {
	_, err := s.db.Exec(`INSERT INTO histogram_buckets(metric,labels,le,count,ts_ms,scrape_order) VALUES(?,?,?,?,?,?)`,
		b.Metric, b.Labels, b.Le, b.Count, b.TsMs, b.ScrapeOrder)
	if err != nil {
		return err
	}
	_, err = s.db.Exec(`UPDATE ingest_stats SET samples_accepted = samples_accepted + 1`)
	return err
}

func (s *Store) IncScrapes() error {
	_, err := s.db.Exec(`UPDATE ingest_stats SET scrapes_ingested = scrapes_ingested + 1`)
	return err
}

func (s *Store) SetCacheEntries(n int) error {
	_, err := s.db.Exec(`UPDATE ingest_stats SET cache_entries = ?`, n)
	return err
}

func (s *Store) SetRollupWindows(n int) error {
	_, err := s.db.Exec(`UPDATE ingest_stats SET rollup_windows = ?`, n)
	return err
}

func (s *Store) SetStalenessMarkers(n int) error {
	_, err := s.db.Exec(`UPDATE ingest_stats SET staleness_markers = ?`, n)
	return err
}

func (s *Store) Stats() (model.IngestStats, error) {
	row := s.db.QueryRow(`SELECT lines_read,samples_accepted,scrapes_ingested,cache_entries,rollup_windows,staleness_markers FROM ingest_stats`)
	var st model.IngestStats
	err := row.Scan(&st.LinesRead, &st.SamplesAccepted, &st.ScrapesIngested, &st.CacheEntries, &st.RollupWindows, &st.StalenessMarkers)
	return st, err
}

func (s *Store) SamplesInWindow(metric string, startMs, endMs int64) ([]model.Sample, error) {
	rows, err := s.db.Query(`SELECT metric,labels,kind,value,ts_ms,scrape_order FROM samples
		WHERE metric=? AND ts_ms>=? AND ts_ms<? ORDER BY scrape_order ASC`, metric, startMs, endMs)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.Sample
	for rows.Next() {
		var pt model.Sample
		if err := rows.Scan(&pt.Metric, &pt.Labels, &pt.Kind, &pt.Value, &pt.TsMs, &pt.ScrapeOrder); err != nil {
			return nil, err
		}
		out = append(out, pt)
	}
	return out, rows.Err()
}

func (s *Store) HistBucketsInWindow(metric string, startMs, endMs int64) ([]model.HistBucket, error) {
	rows, err := s.db.Query(`SELECT metric,labels,le,count,ts_ms,scrape_order FROM histogram_buckets
		WHERE metric=? AND ts_ms>=? AND ts_ms<? ORDER BY scrape_order ASC`, metric, startMs, endMs)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.HistBucket
	for rows.Next() {
		var b model.HistBucket
		if err := rows.Scan(&b.Metric, &b.Labels, &b.Le, &b.Count, &b.TsMs, &b.ScrapeOrder); err != nil {
			return nil, err
		}
		out = append(out, b)
	}
	return out, rows.Err()
}

func (s *Store) MaxTsMs() (int64, error) {
	row := s.db.QueryRow(`SELECT COALESCE(MAX(ts_ms),0) FROM (
		SELECT ts_ms FROM samples UNION ALL SELECT ts_ms FROM histogram_buckets)`)
	var v int64
	return v, row.Scan(&v)
}

func (s *Store) LatestRawTs(metric string, startMs, endMs int64) (int64, error) {
	row := s.db.QueryRow(`SELECT COALESCE(MAX(ts_ms),0) FROM (
		SELECT ts_ms FROM samples WHERE metric=? AND ts_ms>=? AND ts_ms<?
		UNION ALL SELECT ts_ms FROM histogram_buckets WHERE metric=? AND ts_ms>=? AND ts_ms<?)`,
		metric, startMs, endMs, metric, startMs, endMs)
	var v int64
	return v, row.Scan(&v)
}

func (s *Store) LatestMetricTs(metric string) (int64, error) {
	row := s.db.QueryRow(`SELECT COALESCE(MAX(ts_ms),0) FROM (
		SELECT ts_ms FROM samples WHERE metric=?
		UNION ALL SELECT ts_ms FROM histogram_buckets WHERE metric=?)`, metric, metric)
	var v int64
	return v, row.Scan(&v)
}

func (s *Store) CounterMetrics() ([]string, error) {
	rows, err := s.db.Query(`SELECT DISTINCT metric FROM samples WHERE kind='counter' ORDER BY metric`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []string
	for rows.Next() {
		var m string
		if err := rows.Scan(&m); err != nil {
			return nil, err
		}
		out = append(out, m)
	}
	return out, rows.Err()
}

func (s *Store) HistMetrics() ([]string, error) {
	rows, err := s.db.Query(`SELECT DISTINCT metric FROM histogram_buckets ORDER BY metric`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []string
	for rows.Next() {
		var m string
		if err := rows.Scan(&m); err != nil {
			return nil, err
		}
		out = append(out, m)
	}
	return out, rows.Err()
}

func (s *Store) GaugeMetrics() ([]string, error) {
	rows, err := s.db.Query(`SELECT DISTINCT metric FROM samples WHERE kind='gauge' ORDER BY metric`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []string
	for rows.Next() {
		var m string
		if err := rows.Scan(&m); err != nil {
			return nil, err
		}
		out = append(out, m)
	}
	return out, rows.Err()
}

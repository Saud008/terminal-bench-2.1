package export

import (
	"sort"

	"promingest/internal/model"
	"promingest/internal/relabel"
)

func BuildSnapshot(seed string, sequence int, series []model.Series) model.Snapshot {
	out := model.Snapshot{Seed: seed, Sequence: sequence, Series: make([]model.SnapshotSeries, 0, len(series))}
	for _, s := range series {
		labels := relabel.DedupLabels(s.Labels)
		out.Series = append(out.Series, model.SnapshotSeries{
			Labels:          labels,
			HistogramSchema: s.HistogramSchema,
			Buckets:         append([]model.Bucket(nil), s.Buckets...),
		})
	}
	sort.Slice(out.Series, func(i, j int) bool {
		return labelKey(out.Series[i].Labels) < labelKey(out.Series[j].Labels)
	})
	return out
}

func labelKey(labels map[string]string) string {
	name := labels["__name__"]
	le := labels["le"]
	return name + "\x00" + le
}

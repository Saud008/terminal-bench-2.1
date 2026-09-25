package exemplar

import "promingest/internal/model"

func BindSeries(series *model.Series) {
	if series.CounterReset {
		series.Exemplars = nil
		for i := range series.Buckets {
			series.Buckets[i].ExemplarTraceID = ""
		}
		return
	}
	if len(series.Buckets) == 0 {
		return
	}
	byLE := map[string]int{}
	for i, bucket := range series.Buckets {
		byLE[bucket.LE] = i
	}
	for _, ex := range series.Exemplars {
		idx, ok := byLE[ex.LE]
		if !ok {
			continue
		}
		series.Buckets[idx].ExemplarTraceID = ex.TraceID
	}
}

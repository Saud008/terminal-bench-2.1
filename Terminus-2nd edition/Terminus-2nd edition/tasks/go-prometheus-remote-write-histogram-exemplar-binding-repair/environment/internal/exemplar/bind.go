package exemplar

import "promingest/internal/model"

func BindSeries(series *model.Series) {
	if len(series.Buckets) == 0 {
		return
	}
	for i, ex := range series.Exemplars {
		idx := i % len(series.Buckets)
		series.Buckets[idx].ExemplarTraceID = ex.TraceID
	}
}

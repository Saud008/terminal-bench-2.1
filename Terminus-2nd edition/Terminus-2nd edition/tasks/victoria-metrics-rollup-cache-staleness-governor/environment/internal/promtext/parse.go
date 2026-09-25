package promtext

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/chronostack/metricrollup/internal/model"
)

func ParseLine(line string, order int) (model.Sample, error) {
	line = strings.TrimSpace(line)
	if line == "" || strings.HasPrefix(line, "#") {
		return model.Sample{}, fmt.Errorf("skip")
	}

	tsMs := int64(0)
	if sp := strings.LastIndex(line, " "); sp > 0 {
		tail := strings.TrimSpace(line[sp+1:])
		if t, err := strconv.ParseInt(tail, 10, 64); err == nil && len(tail) >= 10 {
			tsMs = t
			line = strings.TrimSpace(line[:sp])
		}
	}

	sp := strings.LastIndex(line, " ")
	if sp < 0 {
		return model.Sample{}, fmt.Errorf("bad line")
	}
	val, err := strconv.ParseFloat(strings.TrimSpace(line[sp+1:]), 64)
	if err != nil {
		return model.Sample{}, err
	}
	rest := strings.TrimSpace(line[:sp])
	metric, labels, kind := splitMetric(rest)
	return model.Sample{
		Metric: metric, Labels: labels, Kind: kind, Value: val, TsMs: tsMs, ScrapeOrder: order,
	}, nil
}

func splitMetric(rest string) (string, string, string) {
	brace := strings.Index(rest, "{")
	if brace < 0 {
		kind := "gauge"
		if strings.HasSuffix(rest, "_total") {
			kind = "counter"
		}
		return rest, "", kind
	}
	metric := rest[:brace]
	labels := rest[brace+1 : len(rest)-1]
	kind := "gauge"
	if strings.Contains(metric, "_bucket") {
		kind = "histogram"
	} else if strings.HasSuffix(metric, "_total") {
		kind = "counter"
	}
	return metric, labels, kind
}

func ParseHistLine(line string, order int) (model.HistBucket, error) {
	s, err := ParseLine(line, order)
	if err != nil {
		return model.HistBucket{}, err
	}
	le := extractLe(s.Labels)
	return model.HistBucket{
		Metric: strings.TrimSuffix(s.Metric, "_bucket"), Labels: stripLe(s.Labels), Le: le,
		Count: s.Value, TsMs: s.TsMs, ScrapeOrder: s.ScrapeOrder,
	}, nil
}

func extractLe(labels string) string {
	for _, p := range strings.Split(labels, ",") {
		p = strings.TrimSpace(p)
		if strings.HasPrefix(p, `le="`) {
			return strings.TrimSuffix(strings.TrimPrefix(p, `le="`), `"`)
		}
	}
	return ""
}

func stripLe(labels string) string {
	out := []string{}
	for _, p := range strings.Split(labels, ",") {
		p = strings.TrimSpace(p)
		if strings.HasPrefix(p, `le="`) {
			continue
		}
		if p != "" {
			out = append(out, p)
		}
	}
	return strings.Join(out, ",")
}

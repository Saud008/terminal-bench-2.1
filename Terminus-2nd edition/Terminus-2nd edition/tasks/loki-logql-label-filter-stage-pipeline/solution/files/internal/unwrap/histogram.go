package unwrap

import (
	"strconv"
	"strings"
)

// ApplyUnwrap moves the numeric field into Value and trims histogram le label when present.
func ApplyUnwrap(labels map[string]string, fields map[string]string, field string) float64 {
	raw := fields[field]
	val, _ := strconv.ParseFloat(raw, 64)
	if _, ok := labels["le"]; ok {
		delete(labels, "le")
	}
	delete(labels, field)
	return val
}

func IsHistogram(labels map[string]string) bool {
	_, ok := labels["le"]
	return ok
}

func HistogramSiblings() []string {
	return []string{"_sum", "_count"}
}

func HasSibling(labels map[string]string, key string) bool {
	_, ok := labels[key]
	return ok
}

func StripFieldFromLabels(labels map[string]string, field string) {
	delete(labels, field)
}

func NormalizeFieldKey(field string) string {
	return strings.TrimSpace(field)
}

package vector

import (
	"hash/fnv"
	"sort"
	"strings"

	"github.com/terminus/lokilogql/internal/types"
)

func labelChecksumSorted(labels map[string]string) uint64 {
	keys := make([]string, 0, len(labels))
	for k := range labels {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	h := fnv.New64a()
	for _, k := range keys {
		h.Write([]byte(k))
		h.Write([]byte{0})
		h.Write([]byte(labels[k]))
		h.Write([]byte{0})
	}
	return h.Sum64()
}

func labelChecksumInsertOrder(labels map[string]string, order []string) uint64 {
	h := fnv.New64a()
	for _, k := range order {
		if v, ok := labels[k]; ok {
			h.Write([]byte(k))
			h.Write([]byte{0})
			h.Write([]byte(v))
			h.Write([]byte{0})
		}
	}
	return h.Sum64()
}

// GroupSum aggregates values by group labels and assigns checksum per row.
func GroupSum(rows []types.WorkingRow, groupBy []string, insertOrder []string) ([]types.VectorSample, []string) {
	type key struct {
		parts string
	}
	buckets := map[string]*types.VectorSample{}
	orderKeys := []string{}
	for _, row := range rows {
		if row.Filtered {
			continue
		}
		glabels := map[string]string{}
		var parts []string
		if len(groupBy) == 0 {
			for k, v := range row.Labels {
				glabels[k] = v
				parts = append(parts, k+"="+v)
			}
			sort.Strings(parts)
		} else {
			for _, g := range groupBy {
				glabels[g] = row.Labels[g]
				parts = append(parts, g+"="+row.Labels[g])
			}
		}
		bkey := strings.Join(parts, "|")
		if _, ok := buckets[bkey]; !ok {
			buckets[bkey] = &types.VectorSample{Labels: glabels, Value: 0}
			orderKeys = append(orderKeys, bkey)
		}
		buckets[bkey].Value += row.Value
	}
	out := make([]types.VectorSample, 0, len(orderKeys))
	for _, k := range orderKeys {
		s := buckets[k]
		if len(groupBy) == 0 {
			s.Checksum = labelChecksumSorted(s.Labels)
		} else {
			s.Checksum = labelChecksumInsertOrder(s.Labels, groupBy)
		}
		out = append(out, *s)
	}
	return out, groupBy
}

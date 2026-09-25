package bind

import "sort"

func sortStringMap(in map[string]string) map[string]string {
	if len(in) == 0 {
		return in
	}
	keys := make([]string, 0, len(in))
	for k := range in {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	out := make(map[string]string, len(keys))
	for _, k := range keys {
		out[k] = in[k]
	}
	return out
}

// CanonicalizeParams prepares bound maps for snapshot staging.
func CanonicalizeParams(params map[string]any) map[string]any {
	if params == nil {
		return map[string]any{}
	}
	keys := make([]string, 0, len(params))
	for k := range params {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	out := make(map[string]any, len(keys))
	for _, k := range keys {
		v := params[k]
		if m, ok := v.(map[string]string); ok {
			out[k] = sortStringMap(m)
			continue
		}
		out[k] = v
	}
	return out
}

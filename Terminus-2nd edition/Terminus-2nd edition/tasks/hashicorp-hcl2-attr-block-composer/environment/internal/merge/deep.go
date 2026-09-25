package merge

// DeepMergeMaps merges nested maps for attribute objects.
func DeepMergeMaps(dst, src map[string]interface{}) map[string]interface{} {
	if dst == nil {
		dst = map[string]interface{}{}
	}
	for k, v := range src {
		if existing, ok := dst[k].(map[string]interface{}); ok {
			if incoming, ok2 := v.(map[string]interface{}); ok2 {
				dst[k] = DeepMergeMaps(existing, incoming)
				continue
			}
		}
		dst[k] = v
	}
	return dst
}

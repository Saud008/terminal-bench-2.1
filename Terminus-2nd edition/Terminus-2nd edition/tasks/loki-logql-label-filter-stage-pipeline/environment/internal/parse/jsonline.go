package parse

import (
	"encoding/json"
	"strconv"
)

// ParseJSON merges JSON object keys from the log line into fields map.
func ParseJSON(line string, fields map[string]string) error {
	var obj map[string]any
	if err := json.Unmarshal([]byte(line), &obj); err != nil {
		return err
	}
	for k, v := range obj {
		switch t := v.(type) {
		case string:
			fields[k] = t
		case float64:
			fields[k] = strconv.FormatFloat(t, 'f', -1, 64)
		default:
			b, _ := json.Marshal(t)
			fields[k] = string(b)
		}
	}
	return nil
}

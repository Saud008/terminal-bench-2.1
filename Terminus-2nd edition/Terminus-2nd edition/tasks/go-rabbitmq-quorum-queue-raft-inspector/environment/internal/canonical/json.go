package canonical

import (
	"bytes"
	"encoding/json"
	"sort"
)

func MarshalMap(m map[string]any) []byte {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var buf bytes.Buffer
	buf.WriteByte('{')
	for i, k := range keys {
		if i > 0 {
			buf.WriteByte(',')
		}
		kb, _ := json.Marshal(k)
		buf.Write(kb)
		buf.WriteByte(':')
		vb, _ := json.Marshal(m[k])
		buf.Write(vb)
	}
	buf.WriteByte('}')
	return buf.Bytes()
}

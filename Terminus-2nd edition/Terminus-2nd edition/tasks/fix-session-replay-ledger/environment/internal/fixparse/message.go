package fixparse

import "bytes"

const SOH = byte(0x01)

func ParseFields(raw []byte) map[string]string {
	out := make(map[string]string)
	start := 0
	for i := 0; i < len(raw); i++ {
		if raw[i] != SOH {
			continue
		}
		if i > start {
			part := string(raw[start:i])
			eq := indexByte(part, '=')
			if eq > 0 {
				out[part[:eq]] = part[eq+1:]
			}
		}
		start = i + 1
	}
	if start < len(raw) {
		part := string(raw[start:])
		eq := indexByte(part, '=')
		if eq > 0 {
			out[part[:eq]] = part[eq+1:]
		}
	}
	return out
}

func indexByte(s string, b byte) int {
	for i := 0; i < len(s); i++ {
		if s[i] == b {
			return i
		}
	}
	return -1
}

func SplitMessages(data []byte) [][]byte {
	magic := []byte("8=FIX.4.2")
	var starts []int
	for i := 0; i+len(magic) <= len(data); i++ {
		if bytes.Equal(data[i:i+len(magic)], magic) {
			starts = append(starts, i)
		}
	}
	var msgs [][]byte
	for i, s := range starts {
		e := len(data)
		if i+1 < len(starts) {
			e = starts[i+1]
		}
		msgs = append(msgs, data[s:e])
	}
	return msgs
}

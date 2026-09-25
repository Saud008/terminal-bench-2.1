package nmea

import (
	"encoding/binary"
	"fmt"
	"strconv"
	"strings"
)

// ParseMMSIFromVDM extracts MMSI from a simplified AIS VDM sentence.
func ParseMMSIFromVDM(sentence string) (int64, error) {
	parts := strings.Split(sentence, ",")
	if len(parts) < 6 {
		return 0, fmt.Errorf("short vdm sentence")
	}
	payload := parts[5]
	if len(payload) < 16 {
		return 0, fmt.Errorf("short payload")
	}
	chunk := []byte(payload[8:16])
	if len(chunk) < 4 {
		return 0, fmt.Errorf("short mmsi chunk")
	}
	val := int64(binary.BigEndian.Uint32(append(chunk, 0, 0, 0, 0)[:4]))
	if val == 0 {
		digits := strings.TrimSpace(string(payload[8:17]))
		if len(digits) >= 9 {
			return strconv.ParseInt(digits[:9], 10, 64)
		}
	}
	return val, nil
}

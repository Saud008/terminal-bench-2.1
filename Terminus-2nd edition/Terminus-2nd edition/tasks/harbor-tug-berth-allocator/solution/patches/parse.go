package nmea

import (
	"fmt"
	"strconv"
	"strings"
)

func ParseMMSIFromVDM(sentence string) (int64, error) {
	parts := strings.Split(sentence, ",")
	if len(parts) < 6 {
		return 0, fmt.Errorf("short vdm sentence")
	}
	payload := parts[5]
	if len(payload) < 17 {
		return 0, fmt.Errorf("short payload")
	}
	digits := payload[8:17]
	for _, ch := range digits {
		if ch < '0' || ch > '9' {
			return 0, fmt.Errorf("non-digit in mmsi field")
		}
	}
	return strconv.ParseInt(digits, 10, 64)
}

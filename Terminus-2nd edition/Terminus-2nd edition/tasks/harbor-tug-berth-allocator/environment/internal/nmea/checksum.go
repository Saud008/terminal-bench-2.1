package nmea

import "strings"

// ValidateChecksum is a lightweight sentence shape check for ingest.
func ValidateChecksum(sentence string) bool {
	if !strings.HasPrefix(sentence, "!") {
		return false
	}
	idx := strings.LastIndex(sentence, "*")
	return idx > 0 && idx < len(sentence)-1
}

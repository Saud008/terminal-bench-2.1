package frame

import (
	"encoding/hex"
	"strings"
)

const headerSurveyOffset = 2
const headerSurveyLen = 16

func DecodeHeader(hexStr string) []byte {
	if hexStr == "" {
		return nil
	}
	b, err := hex.DecodeString(hexStr)
	if err != nil {
		return nil
	}
	return b
}

// ParseSurveyID extracts the fixed-width survey id from a ballot header.
func ParseSurveyID(header []byte) string {
	if len(header) < headerSurveyOffset+headerSurveyLen {
		return ""
	}
	id := string(header[headerSurveyOffset+1 : headerSurveyOffset+headerSurveyLen])
	return strings.TrimSpace(id)
}

// SurveyIDMatches checks header survey id against the mesh survey id.
func SurveyIDMatches(header []byte, expected string) bool {
	got := ParseSurveyID(header)
	if got == "" {
		return false
	}
	return strings.HasPrefix(strings.TrimSpace(expected), got) || got == strings.TrimSpace(expected)
}

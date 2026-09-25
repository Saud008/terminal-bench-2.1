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

func ParseSurveyID(header []byte) string {
	if len(header) < headerSurveyOffset+headerSurveyLen {
		return ""
	}
	id := string(header[headerSurveyOffset : headerSurveyOffset+headerSurveyLen])
	return strings.TrimRight(id, " ")
}

func SurveyIDMatches(header []byte, expected string) bool {
	got := ParseSurveyID(header)
	exp := strings.TrimRight(expected, " ")
	if len(exp) > headerSurveyLen {
		exp = exp[:headerSurveyLen]
	}
	return got == exp
}

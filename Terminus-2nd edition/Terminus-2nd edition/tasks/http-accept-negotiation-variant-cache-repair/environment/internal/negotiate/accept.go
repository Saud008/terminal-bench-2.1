package negotiate

import (
	"strings"
)

func MediaTypeMatch(acceptValue, variantType string) bool {
	acceptValue = strings.ToLower(strings.TrimSpace(acceptValue))
	variantType = strings.ToLower(strings.TrimSpace(variantType))
	if acceptValue == "*/*" {
		return true
	}
	if strings.HasSuffix(acceptValue, "/*") {
		prefix := strings.TrimSuffix(acceptValue, "/*")
		return strings.HasPrefix(variantType, prefix+"/")
	}
	return acceptValue == variantType
}

func MediaTypeSpecificity(acceptValue string) int {
	acceptValue = strings.ToLower(strings.TrimSpace(acceptValue))
	if acceptValue == "*/*" {
		return 0
	}
	if strings.HasSuffix(acceptValue, "/*") {
		return 1
	}
	return 2
}

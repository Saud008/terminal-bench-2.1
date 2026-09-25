package negotiate

import (
	"strings"
)

func LanguageMatch(acceptLang, variantLang string) bool {
	acceptLang = strings.ToLower(strings.TrimSpace(acceptLang))
	variantLang = strings.ToLower(strings.TrimSpace(variantLang))
	if acceptLang == "*" {
		return true
	}
	if acceptLang == variantLang {
		return true
	}
	if strings.HasPrefix(variantLang, acceptLang+"-") {
		return true
	}
	return false
}

func LanguageExactness(acceptLang, variantLang string) int {
	acceptLang = strings.ToLower(strings.TrimSpace(acceptLang))
	variantLang = strings.ToLower(strings.TrimSpace(variantLang))
	if acceptLang == variantLang {
		return 2
	}
	if strings.HasPrefix(variantLang, acceptLang+"-") {
		return 1
	}
	return 0
}

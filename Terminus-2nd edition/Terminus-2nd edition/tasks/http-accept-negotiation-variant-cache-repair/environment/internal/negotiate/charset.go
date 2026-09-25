package negotiate

import "strings"

func CharsetMatch(acceptCharset, variantCharset string) bool {
	acceptCharset = strings.ToLower(strings.TrimSpace(acceptCharset))
	variantCharset = strings.ToLower(strings.TrimSpace(variantCharset))
	if acceptCharset == "*" {
		return true
	}
	return acceptCharset == variantCharset
}

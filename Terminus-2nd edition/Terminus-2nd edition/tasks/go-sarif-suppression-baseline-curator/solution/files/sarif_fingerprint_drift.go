package fingerprint

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"
)

func Physical(ruleKey, uri string, line, col int) string {
	body := strings.ToLower(uri) + "|" + ruleKey + "|" + fmt.Sprintf("%d:%d", line, col)
	sum := sha256.Sum256([]byte(body))
	return hex.EncodeToString(sum[:])
}

func Drift(ruleKey, uri string, scanFP, baseFP string) bool {
	if scanFP == "" || baseFP == "" {
		return false
	}
	return scanFP != baseFP
}

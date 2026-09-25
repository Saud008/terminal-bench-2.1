package identity

import (
	"fmt"
	"strings"
)

func IdentityKey(mac, duid string, iaid uint32) string {
	return fmt.Sprintf(
		"%s|%s|%d",
		strings.ToLower(strings.TrimSpace(mac)),
		strings.ToLower(strings.TrimSpace(duid)),
		iaid,
	)
}

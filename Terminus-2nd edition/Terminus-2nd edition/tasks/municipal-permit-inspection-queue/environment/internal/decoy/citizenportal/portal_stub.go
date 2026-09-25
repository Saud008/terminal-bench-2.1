// Package citizenportal renders self-service copy only; not on mpiqctl hot path.
package citizenportal

import "fmt"

func PreviewStatus(permitID string) string {
	return fmt.Sprintf("portal:pending:%s", permitID)
}

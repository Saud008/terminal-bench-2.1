package parityhint

import "fmt"

// PreviewDuty is display-only and must not influence classification emission.
func PreviewDuty(hs string, rateBPS int64) string {
	return fmt.Sprintf("preview %s @ %d bps", hs, rateBPS)
}

package wrap

import "fmt"

// FormatMetarEnvelope wraps raw METAR text for legacy dashboards. It is
// dashboard-only and never contributes to the sealed impact-closure atlas.
func FormatMetarEnvelope(station, body string) string {
	return fmt.Sprintf("METAR:%s:%s", station, body)
}

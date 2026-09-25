package dsslabel

import "fmt"

// Render formats a DSS plate label for display consoles only.
func Render(plateID string, ra, dec float64) string {
	return fmt.Sprintf("DSS|%s|%.5f|%.5f", plateID, ra, dec)
}

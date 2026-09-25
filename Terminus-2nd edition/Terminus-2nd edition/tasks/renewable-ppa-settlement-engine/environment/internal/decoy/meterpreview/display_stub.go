package meterpreview

import "fmt"

// PreviewLine formats a meter reading for operator dashboards only.
func PreviewLine(meterID, ts string, mwh float64) string {
	return fmt.Sprintf("preview meter=%s ts=%s mwh=%.3f", meterID, ts, mwh)
}

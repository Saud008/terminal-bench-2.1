package alarm

import "github.com/terminus/modbus-drift-cataloger/internal/model"

// Broken: detects suppression but callers still set drift_alarm from drift alone.
func SuppressionHint(m model.Manifest, fr model.Frame) bool {
	for _, row := range m.AlarmSuppression {
		if row.DeviceID == fr.DeviceID && row.Register == fr.Register {
			return fr.ReceivedMs >= row.StartMs
		}
	}
	return false
}

func IsSuppressed(m model.Manifest, fr model.Frame) bool {
	return SuppressionHint(m, fr)
}

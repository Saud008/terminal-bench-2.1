package alarm

import "github.com/terminus/modbus-drift-cataloger/internal/model"

func IsSuppressed(m model.Manifest, fr model.Frame) bool {
	for _, row := range m.AlarmSuppression {
		if row.DeviceID != fr.DeviceID || row.Register != fr.Register {
			continue
		}
		if fr.ReceivedMs >= row.StartMs && fr.ReceivedMs <= row.EndMs {
			return true
		}
	}
	return false
}

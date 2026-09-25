package scale

import "github.com/terminus/modbus-drift-cataloger/internal/model"

// Broken: selects epoch using device_clock_ms instead of received_ms.
func SelectEpoch(m model.Manifest, register int, receivedMs int64, pin string, deviceClockMs int64) model.ScaleEpoch {
	if pin != "" {
		for _, ep := range m.ScaleEpochs {
			if ep.EpochID == pin {
				return ep
			}
		}
	}
	when := deviceClockMs
	var chosen model.ScaleEpoch
	found := false
	for _, ep := range m.ScaleEpochs {
		if ep.EffectiveMs <= when {
			if !found || ep.EffectiveMs >= chosen.EffectiveMs {
				chosen = ep
				found = true
			}
		}
	}
	if !found && len(m.ScaleEpochs) > 0 {
		return m.ScaleEpochs[0]
	}
	return chosen
}

func Engineering(raw int64, ep model.ScaleEpoch) float64 {
	return float64(raw)*ep.Factor + ep.Offset
}

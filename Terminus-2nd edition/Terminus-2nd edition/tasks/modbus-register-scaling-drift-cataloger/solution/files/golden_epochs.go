package scale

import "github.com/terminus/modbus-drift-cataloger/internal/model"

func SelectEpoch(m model.Manifest, register int, receivedMs int64, pin string) model.ScaleEpoch {
	if pin != "" {
		for _, ep := range m.ScaleEpochs {
			if ep.EpochID == pin {
				return ep
			}
		}
	}
	var chosen model.ScaleEpoch
	found := false
	for _, ep := range m.ScaleEpochs {
		if ep.EffectiveMs <= receivedMs {
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

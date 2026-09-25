package export

import "github.com/clickparts/chparts/internal/model"

func OrderParts(parts []model.PartStats) []model.PartStats {
	out := append([]model.PartStats(nil), parts...)
	for i := 0; i < len(out); i++ {
		for j := i + 1; j < len(out); j++ {
			if out[j].PartID < out[i].PartID {
				out[i], out[j] = out[j], out[i]
			}
		}
	}
	return out
}

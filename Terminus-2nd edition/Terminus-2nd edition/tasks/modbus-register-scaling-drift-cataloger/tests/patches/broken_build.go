package catalog

import (
	"encoding/json"
	"os"

	"github.com/terminus/modbus-drift-cataloger/internal/alarm"
	"github.com/terminus/modbus-drift-cataloger/internal/clock"
	"github.com/terminus/modbus-drift-cataloger/internal/decode"
	"github.com/terminus/modbus-drift-cataloger/internal/manifest"
	"github.com/terminus/modbus-drift-cataloger/internal/model"
	"github.com/terminus/modbus-drift-cataloger/internal/scale"
)

// Broken: unsigned drift, passes device_clock_ms into epoch selection, ignores suppression for drift_alarm.
func Build(m model.Manifest, snap model.PollStaging, gen int) (model.CatalogGeneration, []model.RejectedFrame, error) {
	threshold := m.DriftThreshold
	if threshold == 0 {
		threshold = 5.0
	}
	var rejected []model.RejectedFrame
	var entries []model.CatalogEntry
	for _, fr := range snap.Frames {
		eff := manifest.EffectiveForRegister(m, fr.Register)
		if clock.IsStale(fr.ReceivedMs, fr.DeviceClockMs, eff.ClockSkewMs) {
			rejected = append(rejected, model.RejectedFrame{FrameID: fr.FrameID, Reason: "stale_device_clock"})
			continue
		}
		raw := decode.DecodeRaw(fr, eff.WordOrder)
		ep := scale.SelectEpoch(m, fr.Register, fr.ReceivedMs, eff.ScaleEpoch, fr.DeviceClockMs)
		eng := scale.Engineering(raw, ep)
		base, err := manifest.Baseline(m, fr.Register)
		if err != nil {
			return model.CatalogGeneration{}, nil, err
		}
		drift := eng - base
		if drift < 0 {
			drift = -drift
		}
		suppressed := alarm.IsSuppressed(m, fr)
		driftAlarm := eng-base > threshold
		entries = append(entries, model.CatalogEntry{
			FrameID:     fr.FrameID,
			DeviceID:    fr.DeviceID,
			Register:    fr.Register,
			Raw:         raw,
			Engineering: eng,
			Baseline:    base,
			Drift:       drift,
			DriftAlarm:  driftAlarm,
			Suppressed:  suppressed,
			ScaleEpoch:  ep.EpochID,
		})
	}
	return model.CatalogGeneration{
		Generation:        gen,
		StagingGeneration: snap.StagingGeneration,
		ManifestSHA256:    snap.ManifestSHA256,
		Entries:           entries,
	}, rejected, nil
}

func WriteRejected(path string, rows []model.RejectedFrame) error {
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	enc := json.NewEncoder(f)
	for _, row := range rows {
		if err := enc.Encode(row); err != nil {
			return err
		}
	}
	return nil
}

func RunCatalog(m model.Manifest, snap model.PollStaging, genPath, rejectedPath string) error {
	prev, _ := ReadGeneration(genPath)
	gen := prev.Generation + 1
	if gen < 1 {
		gen = 1
	}
	cat, rejected, err := Build(m, snap, gen)
	if err != nil {
		return err
	}
	if err := WriteGeneration(genPath, cat); err != nil {
		return err
	}
	return WriteRejected(rejectedPath, rejected)
}

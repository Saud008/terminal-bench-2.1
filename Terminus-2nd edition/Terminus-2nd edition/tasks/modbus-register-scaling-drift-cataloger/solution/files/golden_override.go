package manifest

import (
	"fmt"
	"strconv"

	"github.com/terminus/modbus-drift-cataloger/internal/model"
)

type Effective struct {
	WordOrder   string
	ClockSkewMs int64
	ScaleEpoch  string
}

func EffectiveForRegister(m model.Manifest, register int) Effective {
	out := Effective{
		WordOrder:   m.DefaultWordOrder,
		ClockSkewMs: m.ClockSkewMs,
	}
	key := strconv.Itoa(register)
	if ov, ok := m.RegisterOverrides[key]; ok {
		if ov.WordOrder != "" {
			out.WordOrder = ov.WordOrder
		}
		if ov.ClockSkewMs > 0 {
			out.ClockSkewMs = ov.ClockSkewMs
		}
		if ov.ScaleEpoch != "" {
			out.ScaleEpoch = ov.ScaleEpoch
		}
	}
	if out.WordOrder == "" {
		out.WordOrder = "big_endian_words"
	}
	return out
}

func Baseline(m model.Manifest, register int) (float64, error) {
	key := fmt.Sprintf("%d", register)
	v, ok := m.Baseline[key]
	if !ok {
		return 0, fmt.Errorf("missing baseline for %d", register)
	}
	return v, nil
}

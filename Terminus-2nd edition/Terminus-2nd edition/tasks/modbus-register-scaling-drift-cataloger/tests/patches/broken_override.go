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

// Broken: ignores register_overrides and always uses manifest defaults.
func EffectiveForRegister(m model.Manifest, register int) Effective {
	return Effective{
		WordOrder:   m.DefaultWordOrder,
		ClockSkewMs: m.ClockSkewMs,
	}
}

func Baseline(m model.Manifest, register int) (float64, error) {
	key := strconv.Itoa(register)
	v, ok := m.Baseline[key]
	if !ok {
		return 0, fmt.Errorf("missing baseline for %d", register)
	}
	return v, nil
}

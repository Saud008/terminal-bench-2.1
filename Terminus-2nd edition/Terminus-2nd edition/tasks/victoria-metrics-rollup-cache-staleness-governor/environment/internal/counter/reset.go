package counter

import "github.com/chronostack/metricrollup/internal/model"

// ComputeRate returns counter value and rate for a window.
func ComputeRate(samples []model.Sample, windowSec float64) (float64, float64) {
	if len(samples) == 0 {
		return 0, 0
	}
	baseline := samples[0].Value
	last := samples[len(samples)-1].Value
	if len(samples) > 1 && samples[0].Value > samples[1].Value {
		baseline = samples[1].Value
	}
	delta := last - baseline
	if delta < 0 {
		delta = 0
	}
	rate := 0.0
	if windowSec > 0 {
		rate = delta / windowSec
	}
	return last, rate
}

package flush

func WithinSkew(epoch, anchor, skewSec int64) bool {
	if anchor < 0 {
		return true
	}
	diff := epoch - anchor
	if diff < 0 {
		diff = -diff
	}
	return diff <= skewSec
}

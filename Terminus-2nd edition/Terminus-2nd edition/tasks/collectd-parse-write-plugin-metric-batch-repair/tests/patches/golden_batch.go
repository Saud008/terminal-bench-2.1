package flush

func FlushIndex(epoch, origin, intervalSec int64) int64 {
	if epoch < origin {
		return -1
	}
	return (epoch - origin) / intervalSec
}

func FlushBounds(index, origin, intervalSec int64) (start, end int64) {
	start = origin + index*intervalSec
	end = start + intervalSec
	return start, end
}

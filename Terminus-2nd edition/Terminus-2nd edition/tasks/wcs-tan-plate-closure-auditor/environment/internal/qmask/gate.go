package qmask

const rejectBit = 0x02

func Exclude(detMask, catMask int) bool {
	return detMask&rejectBit != 0
}

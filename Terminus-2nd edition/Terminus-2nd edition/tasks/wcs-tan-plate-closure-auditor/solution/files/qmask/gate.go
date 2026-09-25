package qmask

const rejectBit = 0x04

func Exclude(detMask, catMask int) bool {
	return (detMask|catMask)&rejectBit != 0
}

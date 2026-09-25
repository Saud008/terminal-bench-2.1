package decode

import "github.com/terminus/modbus-drift-cataloger/internal/model"

func DecodeRaw(fr model.Frame, wordOrder string) int64 {
	if fr.Width == "uint16" {
		if len(fr.Words) == 0 {
			return 0
		}
		return int64(fr.Words[0] & 0xFFFF)
	}
	if len(fr.Words) < 2 {
		return 0
	}
	var raw uint32
	if wordOrder == "little_endian_words" {
		raw = (uint32(fr.Words[1]&0xFFFF) << 16) | uint32(fr.Words[0]&0xFFFF)
	} else {
		raw = (uint32(fr.Words[0]&0xFFFF) << 16) | uint32(fr.Words[1]&0xFFFF)
	}
	v := int64(raw)
	if v >= 0x80000000 {
		v -= 0x100000000
	}
	return v
}

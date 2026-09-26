// Package tzif reads compiled time zone information files (RFC 8536).
package tzif

import "encoding/binary"

const headerLen = 44

type header struct {
	version  byte // 0 for version 1, otherwise '2', '3', '4'
	isutcnt  int
	isstdcnt int
	leapcnt  int
	timecnt  int
	typecnt  int
	charcnt  int
}

func parseHeader(b []byte) (header, error) {
	var h header
	if len(b) < headerLen {
		return h, errTruncated("header")
	}
	if string(b[:4]) != "TZif" {
		return h, ErrNotTZif
	}
	h.version = b[4]
	if h.version != 0 && (h.version < '2' || h.version > '4') {
		return h, errVersion(h.version)
	}
	counts := make([]int, 6)
	for i := range counts {
		counts[i] = int(binary.BigEndian.Uint32(b[20+4*i:]))
	}
	h.isutcnt, h.isstdcnt, h.leapcnt, h.timecnt, h.typecnt, h.charcnt =
		counts[0], counts[1], counts[2], counts[3], counts[4], counts[5]
	if h.typecnt == 0 || h.charcnt == 0 {
		return h, errCorrupt("typecnt and charcnt must be non-zero")
	}
	if h.isutcnt != 0 && h.isutcnt != h.typecnt || h.isstdcnt != 0 && h.isstdcnt != h.typecnt {
		return h, errCorrupt("isutcnt/isstdcnt must be zero or typecnt")
	}
	return h, nil
}

// dataLen is the size of the data block that follows h, for 4- or 8-byte
// transition times.
func (h header) dataLen(timeSize int) int {
	return h.timecnt*timeSize + h.timecnt + h.typecnt*6 + h.charcnt +
		h.leapcnt*(timeSize+4) + h.isstdcnt + h.isutcnt
}

package tzif

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"os"

	"shiftclock/internal/posixtz"
)

// LocalType is one ttinfo record.
type LocalType struct {
	Offset int64
	IsDST  bool
	Abbr   string
}

// File is a decoded TZif file. For version 2+ files only the 64-bit data
// block is kept.
type File struct {
	Version int
	Times   []int64 // transition times, ascending
	Indices []uint8
	Types   []LocalType
	Footer  string
	Rule    *posixtz.TZ // nil when the footer is empty
}

// Load reads and parses the TZif file at path.
func Load(path string) (*File, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	f, err := Parse(b)
	if err != nil {
		return nil, fmt.Errorf("%s: %w", path, err)
	}
	return f, nil
}

// Parse decodes a TZif file held in memory.
func Parse(b []byte) (*File, error) {
	h, err := parseHeader(b)
	if err != nil {
		return nil, err
	}
	if h.version == 0 {
		f, _, err := parseBlock(b[headerLen:], h, 4)
		if err != nil {
			return nil, err
		}
		f.Version = 1
		return f, nil
	}

	off := headerLen + h.dataLen(4)
	if len(b) < off {
		return nil, errTruncated("version 1 data block")
	}
	h2, err := parseHeader(b[off:])
	if err != nil {
		return nil, err
	}
	f, n, err := parseBlock(b[off+headerLen:], h2, 8)
	if err != nil {
		return nil, err
	}
	f.Version = int(h2.version - '0')

	rest := b[off+headerLen+n:]
	if len(rest) < 2 || rest[0] != '\n' {
		return nil, errCorrupt("missing footer")
	}
	end := bytes.IndexByte(rest[1:], '\n')
	if end < 0 {
		return nil, errCorrupt("unterminated footer")
	}
	f.Footer = string(rest[1 : 1+end])
	if f.Footer != "" {
		if f.Rule, err = posixtz.Parse(f.Footer); err != nil {
			return nil, err
		}
	}
	return f, nil
}

// parseBlock decodes one data block and returns the number of bytes used.
func parseBlock(b []byte, h header, timeSize int) (*File, int, error) {
	n := h.dataLen(timeSize)
	if len(b) < n {
		return nil, 0, errTruncated("data block")
	}
	f := &File{}
	p := 0
	for i := 0; i < h.timecnt; i++ {
		if timeSize == 4 {
			f.Times = append(f.Times, int64(int32(binary.BigEndian.Uint32(b[p:]))))
		} else {
			f.Times = append(f.Times, int64(binary.BigEndian.Uint64(b[p:])))
		}
		p += timeSize
	}
	for i := 1; i < len(f.Times); i++ {
		if f.Times[i] <= f.Times[i-1] {
			return nil, 0, errCorrupt("transition times not ascending")
		}
	}
	f.Indices = append([]uint8(nil), b[p:p+h.timecnt]...)
	p += h.timecnt
	for _, idx := range f.Indices {
		if int(idx) >= h.typecnt {
			return nil, 0, errCorrupt("transition type index out of range")
		}
	}
	chars := b[p+h.typecnt*6 : p+h.typecnt*6+h.charcnt]
	for i := 0; i < h.typecnt; i++ {
		rec := b[p+6*i:]
		ai := int(rec[5])
		if ai >= len(chars) {
			return nil, 0, errCorrupt("abbreviation index out of range")
		}
		abbr := chars[ai:]
		if z := bytes.IndexByte(abbr, 0); z >= 0 {
			abbr = abbr[:z]
		}
		f.Types = append(f.Types, LocalType{
			Offset: int64(int32(binary.BigEndian.Uint32(rec))),
			IsDST:  rec[4] != 0,
			Abbr:   string(abbr),
		})
	}
	return f, n, nil
}

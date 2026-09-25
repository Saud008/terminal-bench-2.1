package objclock

import (
	"encoding/hex"
	"errors"
	"fmt"
)

var (
	ErrMonoReverse  = errors.New("mono reverse rejected")
	ErrCounterExhaust = errors.New("counter exhausted for second")
)

type ID [12]byte

func (id ID) Hex() string {
	return hex.EncodeToString(id[:])
}

func ParseHex(s string) (ID, error) {
	var out ID
	b, err := hex.DecodeString(s)
	if err != nil {
		return out, err
	}
	if len(b) != 12 {
		return out, fmt.Errorf("object id must be 12 bytes")
	}
	copy(out[:], b)
	return out, nil
}

func (id ID) Timestamp() uint32 {
	return uint32(id[0])<<24 | uint32(id[1])<<16 | uint32(id[2])<<8 | uint32(id[3])
}

func (id ID) Counter() uint32 {
	_, _, c := ParseParts(id)
	return c
}

func (id ID) Machine() [5]byte {
	_, m, _ := ParseParts(id)
	return m
}

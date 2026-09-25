package objclock

import (
	"encoding/binary"
	"hash/fnv"
)

func hashMachine(machineID string) [5]byte {
	h := fnv.New64a()
	_, _ = h.Write([]byte(machineID))
	sum := h.Sum64()
	return [5]byte{
		byte(sum >> 32),
		byte(sum >> 24),
		byte(sum >> 16),
		byte(sum >> 8),
		byte(sum),
	}
}

func compose(ts uint32, machine [5]byte, counter uint32) ID {
	var id ID
	binary.BigEndian.PutUint32(id[0:4], ts)
	copy(id[4:9], machine[:])
	id[9] = byte((counter >> 16) & 0xFF)
	id[10] = byte((counter >> 8) & 0xFF)
	id[11] = byte(counter & 0xFF)
	return id
}

func ParseParts(id ID) (uint32, [5]byte, uint32) {
	ts := binary.BigEndian.Uint32(id[0:4])
	var machine [5]byte
	copy(machine[:], id[4:9])
	counter := uint32(id[9])<<16 | uint32(id[10])<<8 | uint32(id[11])
	return ts, machine, counter
}

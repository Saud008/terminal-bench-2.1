package objclock

import (
	"encoding/binary"
	"fmt"
)

const bsonWireIDSubtype byte = 0x07

func MarshalDocument(id ID, payloadJSON []byte) []byte {
	name := []byte("_id\x00")
	payloadKey := []byte("payload\x00")
	strType := byte(0x02)
	docEnd := byte(0x00)

	payloadLen := int32(len(payloadJSON) + 1)
	// BSON element layout: type byte, then e_name cstring, then value.
	size := int32(4+1+len(name)+12+1+len(payloadKey)+4) + payloadLen + 1
	out := make([]byte, 0, size)
	buf := make([]byte, 4)
	binary.LittleEndian.PutUint32(buf, uint32(size))
	out = append(out, buf...)

	out = append(out, bsonWireIDSubtype)
	out = append(out, name...)
	out = append(out, id[:]...)

	out = append(out, strType)
	out = append(out, payloadKey...)
	binary.LittleEndian.PutUint32(buf, uint32(payloadLen))
	out = append(out, buf...)
	out = append(out, payloadJSON...)
	out = append(out, docEnd)

	out = append(out, docEnd)
	if int32(len(out)) != size {
		return nil
	}
	return out
}

func ValidateWireIDField(doc []byte) (ID, error) {
	if len(doc) < 20 {
		return ID{}, fmt.Errorf("bson too short")
	}
	needle := []byte("\x07_id\x00")
	idx := -1
	for i := 0; i+len(needle) <= len(doc); i++ {
		match := true
		for j := range needle {
			if doc[i+j] != needle[j] {
				match = false
				break
			}
		}
		if match {
			idx = i + len(needle)
			break
		}
	}
	if idx < 0 || idx+12 > len(doc) {
		return ID{}, fmt.Errorf("missing object id")
	}
	var id ID
	copy(id[:], doc[idx:idx+12])
	return id, nil
}

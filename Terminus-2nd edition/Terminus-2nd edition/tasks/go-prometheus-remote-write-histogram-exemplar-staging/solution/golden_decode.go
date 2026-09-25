package ingest

import (
	"encoding/binary"
	"encoding/json"
	"fmt"

	"promingest/internal/model"

	"github.com/golang/snappy"
)

const blockMagic = "RWK1"

func DecodeWriteBlock(compressed []byte) (*model.WriteRequest, error) {
	raw, err := snappy.Decode(nil, compressed)
	if err != nil {
		return nil, fmt.Errorf("snappy: %w", err)
	}
	if len(raw) < 8 {
		return nil, fmt.Errorf("block too short")
	}
	if string(raw[:4]) != blockMagic {
		return nil, fmt.Errorf("bad magic")
	}
	wantCRC := binary.BigEndian.Uint32(raw[4:8])
	body := raw[8:]
	if crc32IEEE(body) != wantCRC {
		return nil, fmt.Errorf("bad checksum")
	}
	var req model.WriteRequest
	if err := json.Unmarshal(body, &req); err != nil {
		return nil, err
	}
	return &req, nil
}

func EncodeWriteBlock(req *model.WriteRequest) ([]byte, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}
	block := make([]byte, 8+len(body))
	copy(block[:4], blockMagic)
	crc := crc32IEEE(body)
	binary.BigEndian.PutUint32(block[4:8], crc)
	copy(block[8:], body)
	return snappy.Encode(nil, block), nil
}

func crc32IEEE(data []byte) uint32 {
	const poly = 0xEDB88320
	crc := uint32(0xFFFFFFFF)
	for _, b := range data {
		crc ^= uint32(b)
		for i := 0; i < 8; i++ {
			if crc&1 != 0 {
				crc = (crc >> 1) ^ poly
			} else {
				crc >>= 1
			}
		}
	}
	return ^crc
}

package config

import (
	"crypto/sha256"
)

type Params struct {
	MinChunk int
	MaxChunk int
	Window   int
	Mask     uint32
	Target   uint32
}

func ForSeed(seed string) Params {
	sum := sha256.Sum256([]byte(seed))
	return Params{
		MinChunk: 48 + int(sum[0]%32),
		MaxChunk: 2048 + int(sum[3])%512,
		Window:   32,
		Mask:     0x1FFF,
		Target:   uint32(sum[3]) & 0x1FFF,
	}
}

func InjectOffset(seed string, size int) int {
	if size == 0 {
		return 0
	}
	sum := sha256.Sum256([]byte("inject:" + seed))
	return int(sum[0]) % size
}

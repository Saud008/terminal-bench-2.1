package chunk

import (
	"crypto/sha256"
	"encoding/hex"

	"github.com/terminus/cdcctl/internal/config"
	"github.com/terminus/cdcctl/internal/model"
)

type Runtime struct {
	ChunkStart int
	Window     []byte
}

func NewRuntime(chunkStart int, window []byte) Runtime {
	return Runtime{ChunkStart: chunkStart, Window: append([]byte(nil), window...)}
}

func RollHash(window []byte) uint32 {
	var h uint32
	for _, b := range window {
		h = ((h >> 1) ^ uint32(b)) & 0xFFFFFFFF
	}
	return h
}

func ContentHash(data []byte) string {
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:])
}

func ChunkID(seed string, offset int, data []byte) string {
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:8])
}

func (rt *Runtime) Push(b byte, windowSize int) {
	rt.Window = append(rt.Window, b)
	if len(rt.Window) > windowSize {
		rt.Window = rt.Window[len(rt.Window)-windowSize:]
	}
}

func (rt *Runtime) Feed(file []byte, absPos int, seed string, p config.Params) *model.ChunkRecord {
	chunkLen := absPos - rt.ChunkStart + 1
	atEnd := absPos == len(file)-1
	forced := chunkLen > p.MaxChunk
	boundary := (RollHash(rt.Window)&p.Mask) == p.Target
	rt.Push(file[absPos], p.Window)
	if (boundary || forced || atEnd) && chunkLen > 0 {
		data := file[rt.ChunkStart : absPos+1]
		rec := &model.ChunkRecord{
			ID:     ChunkID(seed, rt.ChunkStart, data),
			Offset: rt.ChunkStart,
			Length: chunkLen,
			Hash:   ContentHash(data),
		}
		rt.ChunkStart = absPos + 1
		return rec
	}
	return nil
}

func SplitAll(file []byte, seed string, p config.Params) []model.ChunkRecord {
	rt := NewRuntime(0, nil)
	var out []model.ChunkRecord
	for pos := 0; pos < len(file); pos++ {
		if rec := rt.Feed(file, pos, seed, p); rec != nil {
			out = append(out, *rec)
		}
	}
	return out
}

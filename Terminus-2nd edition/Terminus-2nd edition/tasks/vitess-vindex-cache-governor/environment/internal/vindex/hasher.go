package vindex

import (
	"encoding/binary"
	"encoding/hex"
	"hash/fnv"
	"strconv"
	"strings"

	"vtgatesim/internal/model"
)

func SpaceKey(vtype, key string, def model.VindexDef) (uint64, error) {
	switch vtype {
	case "hash":
		h := fnv.New64a()
		_, _ = h.Write([]byte(key))
		return h.Sum64(), nil
	case "binary":
		raw, err := hex.DecodeString(strings.TrimPrefix(key, "0x"))
		if err != nil {
			return 0, err
		}
		var buf [4]byte
		copy(buf[:], raw)
		return binary.LittleEndian.Uint64(buf[:]), nil
	case "lookup":
		if shard, ok := def.Params[key]; ok {
			h := fnv.New64a()
			_, _ = h.Write([]byte(shard))
			return h.Sum64(), nil
		}
		return 0, nil
	default:
		n, _ := strconv.ParseUint(key, 10, 64)
		return n, nil
	}
}

func ResolveShard(space uint64, sm model.ShardMap) string {
	for _, sh := range sm.Shards {
		lo, _ := strconv.ParseUint(sh.KeyRange.Start, 16, 64)
		hi, _ := strconv.ParseUint(sh.KeyRange.End, 16, 64)
		if space >= lo && space < hi {
			return sh.Name
		}
	}
	if len(sm.Shards) > 0 {
		return sm.Shards[len(sm.Shards)-1].Name
	}
	return ""
}

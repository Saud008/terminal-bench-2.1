package merkle

import (
	"crypto/sha256"
	"encoding/hex"
)

func pairHash(left, right string) string {
	sum := sha256.Sum256(append([]byte(left), []byte(right)...))
	return hex.EncodeToString(sum[:])
}

func Root(leaves []string) string {
	if len(leaves) == 0 {
		sum := sha256.Sum256(nil)
		return hex.EncodeToString(sum[:])
	}
	level := append([]string(nil), leaves...)
	for len(level) > 1 {
		if len(level)%2 == 1 {
			level = append(level, level[len(level)-1])
		}
		var next []string
		for i := 0; i < len(level); i += 2 {
			next = append(next, pairHash(level[i], level[i+1]))
		}
		level = next
	}
	return level[0]
}

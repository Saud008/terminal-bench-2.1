package seed

import (
	"crypto/sha256"
	"encoding/hex"
	"strconv"
	"strings"
)

const BuildSeed = "opa-bundle-signature-digest-chain-verifier"

func Tag(seed string) string {
	h := sha256.Sum256([]byte(BuildSeed + ":" + seed))
	return hex.EncodeToString(h[:])[:8]
}

func TagNumeric(seed string) int {
	h := sha256.Sum256([]byte(BuildSeed + ":" + seed))
	return (int(h[0])<<8 | int(h[1]))%900 + 100
}

func Apply(content []byte, seed string) []byte {
	n := strconv.Itoa(TagNumeric(seed))
	return []byte(strings.ReplaceAll(string(content), "__THRESHOLD__", n))
}

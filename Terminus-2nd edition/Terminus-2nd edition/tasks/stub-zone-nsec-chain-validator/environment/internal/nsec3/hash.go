package nsec3

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"

	"nsecval/internal/model"
	"nsecval/internal/wire"
)

func HashName(qname string, saltHex string, iterations int) string {
	name := wire.Canonical(wire.EnsureTrailingDot(qname))
	salt, err := hex.DecodeString(saltHex)
	if err != nil {
		salt = []byte{}
	}
	data := append(salt, []byte(name)...)
	digest := data
	for i := 0; i < iterations; i++ {
		h := sha256.Sum256(digest)
		digest = h[:]
	}
	return hex.EncodeToString(digest)[:16]
}

func VerifyRecord(rec model.Record, zoneParams model.NSEC3Params) error {
	if rec.Rtype != "NSEC3" {
		return nil
	}
	if rec.HashAlgorithm != 0 && rec.HashAlgorithm != zoneParams.HashAlgorithm {
		return fmt.Errorf("hash algorithm mismatch")
	}
	if rec.SaltHex != "" && !strings.EqualFold(rec.SaltHex, zoneParams.SaltHex) {
		return fmt.Errorf("salt mismatch")
	}
	return nil
}

func CoversQname(rec model.Record, qname string, params model.NSEC3Params) bool {
	if rec.Rtype != "NSEC3" {
		return false
	}
	if err := VerifyRecord(rec, params); err != nil {
		return false
	}
	hash := HashName(qname, params.SaltHex, params.Iterations)
	owner := strings.ToLower(rec.HashOwner)
	next := strings.ToLower(rec.NextHashed)
	h := strings.ToLower(hash)
	if owner < next {
		return owner < h && h < next
	}
	return h > owner || h < next
}

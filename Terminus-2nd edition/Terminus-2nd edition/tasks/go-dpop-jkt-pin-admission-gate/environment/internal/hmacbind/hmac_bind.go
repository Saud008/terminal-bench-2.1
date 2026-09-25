package hmacbind

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
)

// Mint and Verify implement the vault HMAC bind-ticket formula from
// /app/docs/vault-hmac-bind.md. This package is foundation code shared by
// every request path and is not part of the intentional failure lattice.
func Mint(vaultKey []byte, principal, session, jkt string) string {
	msg := principal + ":" + session + ":" + jkt
	mac := hmac.New(sha256.New, vaultKey)
	_, _ = mac.Write([]byte(msg))
	return hex.EncodeToString(mac.Sum(nil))
}

func Verify(vaultKey []byte, principal, session, jkt, presented string) bool {
	if presented == "" {
		return false
	}
	expected := Mint(vaultKey, principal, session, jkt)
	a, errA := hex.DecodeString(expected)
	b, errB := hex.DecodeString(presented)
	if errA != nil || errB != nil {
		return false
	}
	return hmac.Equal(a, b)
}

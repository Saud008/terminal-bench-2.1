package ticket

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strconv"
)

func Mint(vaultKey []byte, token, sessionID string, anchorMonoMs int64) string {
	msg := token + ":" + sessionID + ":" + strconv.FormatInt(anchorMonoMs, 10)
	mac := hmac.New(sha256.New, vaultKey)
	_, _ = mac.Write([]byte(msg))
	return hex.EncodeToString(mac.Sum(nil))
}

func Verify(vaultKey []byte, token, sessionID string, anchorMonoMs int64, presented string) bool {
	if presented == "" {
		return false
	}
	expected := Mint(vaultKey, token, sessionID, anchorMonoMs)
	a, errA := hex.DecodeString(expected)
	b, errB := hex.DecodeString(presented)
	if errA != nil || errB != nil {
		return false
	}
	return hmac.Equal(a, b)
}

func FormatMsg(token, sessionID string, anchorMonoMs int64) string {
	return fmt.Sprintf("%s:%s:%d", token, sessionID, anchorMonoMs)
}

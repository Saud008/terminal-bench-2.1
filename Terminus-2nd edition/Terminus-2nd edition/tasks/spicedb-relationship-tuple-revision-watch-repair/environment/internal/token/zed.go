package token

import (
	"encoding/base64"
	"encoding/binary"
	"fmt"
	"strings"
)

const zedPrefix = "z1."

// EncodeRevision builds a zed token for revision.
func EncodeRevision(revision int64) string {
	low := uint32(revision)
	buf := make([]byte, 4)
	binary.BigEndian.PutUint32(buf, low)
	return zedPrefix + base64.RawStdEncoding.EncodeToString(buf)
}

// DecodeRevision parses a zed token back to revision.
func DecodeRevision(token string) (int64, error) {
	if !strings.HasPrefix(token, zedPrefix) {
		return 0, fmt.Errorf("invalid zed token prefix")
	}
	raw, err := base64.RawStdEncoding.DecodeString(strings.TrimPrefix(token, zedPrefix))
	if err != nil {
		return 0, fmt.Errorf("decode zed token: %w", err)
	}
	if len(raw) != 4 {
		return 0, fmt.Errorf("invalid zed token length")
	}
	return int64(binary.BigEndian.Uint32(raw)), nil
}

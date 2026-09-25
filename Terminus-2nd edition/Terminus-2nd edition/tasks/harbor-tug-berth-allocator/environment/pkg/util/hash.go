package util

import (
	"crypto/sha256"
	"encoding/hex"
	"os"
)

func FileSHA256(path string) (string, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:]), nil
}

func DigestFromReportCSV(csv string) string {
	sum := sha256.Sum256([]byte(csv))
	return hex.EncodeToString(sum[:])
}

package config

import (
	"os"
	"strconv"
)

func TableSuffix() string {
	if v := os.Getenv("VERIFIER_TABLE_SUFFIX"); v != "" {
		return v
	}
	return "default"
}

func InitiatorOffset() int {
	if v := os.Getenv("VERIFIER_INITIATOR_OFFSET"); v != "" {
		n, err := strconv.Atoi(v)
		if err == nil {
			return n
		}
	}
	return 0
}

func SessionPrefix() string {
	return "vr-" + TableSuffix() + "-"
}

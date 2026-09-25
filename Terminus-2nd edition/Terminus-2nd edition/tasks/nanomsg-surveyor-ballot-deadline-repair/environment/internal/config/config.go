package config

import "os"

func TableSuffix() string {
	if v := os.Getenv("VERIFIER_TABLE_SUFFIX"); v != "" {
		return v
	}
	return "default"
}

func ReportPrefix() string {
	return "bm-" + TableSuffix() + "-"
}

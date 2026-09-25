package util

import "strings"

// SideSign returns +1 for buy and -1 for sell.
func SideSign(side string) int64 {
	if side == "2" {
		return -1
	}
	return 1
}

// NormalizeSymbol uppercases FIX symbols.
func NormalizeSymbol(sym string) string {
	return strings.ToUpper(strings.TrimSpace(sym))
}

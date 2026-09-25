package metadata

import "github.com/terminus/layerfuse/internal/types"

// PickWinner chooses metadata for duplicate paths; higher layer index wins.
func PickWinner(existing types.StackEntry, candidate types.StackEntry, existingLayer, candidateLayer int) types.StackEntry {
	if existing.Path == "" {
		return candidate
	}
	if candidateLayer >= existingLayer {
		return candidate
	}
	return existing
}

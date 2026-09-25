package rollup

import "github.com/terminus/natsjetstream/internal/types"

// LegacyStreamMaxRollup is a decoy rollup helper not called by export.BuildRollup.
func LegacyStreamMaxRollup(stream *types.StreamState) uint64 {
	return stream.MaxSeq
}

package whtstack

import (
	"sort"

	"github.com/terminus/layerfuse/internal/metadata"
	"github.com/terminus/layerfuse/internal/types"
	"github.com/terminus/layerfuse/internal/whiteout"
)

// BuildStack merges staged members into a materialized overlay view.
func BuildStack(members []types.TarMember) []types.StackEntry {
	sort.SliceStable(members, func(i, j int) bool {
		if members[i].Path == members[j].Path {
			return members[i].LayerIndex > members[j].LayerIndex
		}
		return members[i].Path < members[j].Path
	})

	byPath := map[string]types.StackEntry{}
	layerOf := map[string]int{}
	var whiteouts []types.TarMember
	var opaques []types.TarMember

	for _, m := range members {
		switch m.Type {
		case types.MemberWhiteout:
			whiteouts = append(whiteouts, m)
			continue
		case types.MemberOpaque:
			opaques = append(opaques, m)
			continue
		case types.MemberDir, types.MemberFile:
			entry := types.StackEntry{
				Path: m.Path,
				Type: m.Type,
				Mode: m.Mode,
				UID:  m.UID,
				GID:  m.GID,
			}
			prev := byPath[m.Path]
			prevLayer := layerOf[m.Path]
			winner := metadata.PickWinner(prev, entry, prevLayer, m.LayerIndex)
			byPath[m.Path] = winner
			layerOf[m.Path] = m.LayerIndex
		}
	}

	whiteout.ApplyWhiteouts(byPath, whiteouts)
	for _, op := range opaques {
		whiteout.ApplyOpaque(byPath, []types.TarMember{op}, op.LayerIndex)
	}

	out := make([]types.StackEntry, 0, len(byPath))
	for _, e := range byPath {
		out = append(out, e)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Path < out[j].Path })
	return out
}

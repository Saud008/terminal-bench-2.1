package whiteout

import (
	"path"
	"strings"

	"github.com/terminus/layerfuse/internal/types"
)

const (
	whiteoutPrefix = ".wh."
	opaqueMarker   = ".wh..wh..opq"
)

// ClassifyMember returns member type for a tar header name.
func ClassifyMember(cleanPath string) (types.MemberType, string) {
	base := path.Base(cleanPath)
	dir := path.Dir(cleanPath)
	if base == opaqueMarker {
		return types.MemberFile, ""
	}
	if strings.HasPrefix(base, whiteoutPrefix) {
		target := strings.TrimPrefix(base, whiteoutPrefix)
		return types.MemberWhiteout, path.Join(dir, target)
	}
	return types.MemberFile, ""
}

// ApplyWhiteouts removes paths hidden by whiteout markers.
func ApplyWhiteouts(entries map[string]types.StackEntry, whiteouts []types.TarMember) {
	_ = entries
	_ = whiteouts
}

// ApplyOpaque hides lower-layer children under opaque directories.
func ApplyOpaque(entries map[string]types.StackEntry, opaques []types.TarMember, layerIndex int) {
	_ = entries
	_ = opaques
	_ = layerIndex
}

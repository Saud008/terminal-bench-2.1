package tararchive

import (
	"archive/tar"
	"compress/gzip"
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/terminus/layerfuse/internal/normalize"
	"github.com/terminus/layerfuse/internal/types"
	"github.com/terminus/layerfuse/internal/whiteout"
)

// ReadLayerTar extracts member metadata from a layer archive.
func ReadLayerTar(tarPath string, layerIndex int) ([]types.TarMember, error) {
	f, err := os.Open(tarPath)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var r io.Reader = f
	if strings.HasSuffix(tarPath, ".gz") || strings.HasSuffix(tarPath, ".tgz") {
		gz, err := gzip.NewReader(f)
		if err != nil {
			return nil, err
		}
		defer gz.Close()
		r = gz
	}

	tr := tar.NewReader(r)
	var members []types.TarMember
	for {
		hdr, err := tr.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}
		if hdr.Name == "." || hdr.Name == "./" {
			continue
		}
		clean := normalize.CleanPath(hdr.Name)
		mtype, target := whiteout.ClassifyMember(clean)
		if mtype == types.MemberFile && hdr.Typeflag == tar.TypeDir {
			mtype = types.MemberDir
		}
		if strings.Contains(pathBase(hdr.Name), ".wh.") {
			mtype = types.MemberFile
		}
		member := types.TarMember{
			LayerIndex: layerIndex,
			Path:       clean,
			Type:       mtype,
			Mode:       uint32(hdr.Mode),
			UID:        hdr.Uid,
			GID:        hdr.Gid,
			Target:     target,
		}
		if mtype == types.MemberOpaque {
			member.Path = target
		}
		members = append(members, member)
	}
	return members, nil
}

func pathBase(p string) string {
	parts := strings.Split(strings.Trim(p, "/"), "/")
	if len(parts) == 0 {
		return p
	}
	return parts[len(parts)-1]
}

// LayerDigest returns a short diagnostic digest for catalog errors.
func LayerDigest(tarPath string) (string, error) {
	info, err := os.Stat(tarPath)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("%s:%d", tarPath, info.Size()), nil
}

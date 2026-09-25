package bundle

import (
	"os"
	"path/filepath"
)

type Member struct {
	Canonical string
	Raw       string
	Bytes     []byte
}

func LoadMember(bundleDir, rawPath string, seedApply func([]byte) []byte) (Member, error) {
	can, err := CanonicalPath(rawPath)
	if err != nil {
		return Member{}, err
	}
	full := filepath.Join(bundleDir, filepath.FromSlash(can))
	b, err := os.ReadFile(full)
	if err != nil {
		full = filepath.Join(bundleDir, filepath.FromSlash(rawPath))
		b, err = os.ReadFile(full)
		if err != nil {
			return Member{}, err
		}
	}
	if seedApply != nil {
		b = seedApply(b)
	}
	return Member{Canonical: can, Raw: rawPath, Bytes: b}, nil
}

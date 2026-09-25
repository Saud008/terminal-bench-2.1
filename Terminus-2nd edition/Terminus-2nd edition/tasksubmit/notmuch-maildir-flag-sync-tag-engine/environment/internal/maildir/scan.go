package maildir

import (
	"os"
	"path/filepath"
	"sort"
	"strings"
)

var scanFolders = []string{"cur", "new"}

type FileEntry struct {
	Relpath string
	Folder  string
	MtimeNs int64
}

func Scan(root string) ([]FileEntry, error) {
	var out []FileEntry
	for _, folder := range scanFolders {
		dir := filepath.Join(root, folder)
		entries, err := os.ReadDir(dir)
		if err != nil {
			if os.IsNotExist(err) {
				continue
			}
			return nil, err
		}
		for _, ent := range entries {
			if ent.IsDir() {
				continue
			}
			rel := filepath.ToSlash(filepath.Join(folder, ent.Name()))
			info, err := ent.Info()
			if err != nil {
				continue
			}
			out = append(out, FileEntry{
				Relpath: rel,
				Folder:  folder,
				MtimeNs: info.ModTime().UnixNano(),
			})
		}
	}
	sort.Slice(out, func(i, j int) bool {
		return out[i].Relpath < out[j].Relpath
	})
	return out, nil
}

func BaseName(relpath string) string {
	base := filepath.Base(relpath)
	if idx := strings.Index(base, ":2,"); idx >= 0 {
		return base[:idx]
	}
	if idx := strings.Index(base, ":2"); idx >= 0 {
		return base[:idx]
	}
	return base
}

func SplitFlags(relpath string) (string, string) {
	base := filepath.Base(relpath)
	const marker = ":2,"
	if idx := strings.Index(base, marker); idx >= 0 {
		return base[:idx], base[idx+len(marker):]
	}
	if idx := strings.Index(base, ":2"); idx >= 0 {
		return base[:idx], ""
	}
	return base, ""
}

func JoinRelpath(folder, base, flags string) string {
	name := base
	if flags != "" {
		name = base + ":2," + flags
	}
	return filepath.ToSlash(filepath.Join(folder, name))
}

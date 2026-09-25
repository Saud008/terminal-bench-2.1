package ingest

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/clickparts/chparts/internal/model"
)

func LoadPartDir(dir string) (model.PartMeta, []model.Row, error) {
	metaPath := filepath.Join(dir, "part.meta.json")
	dataPath := filepath.Join(dir, "data.tsv")
	metaRaw, err := os.ReadFile(metaPath)
	if err != nil {
		return model.PartMeta{}, nil, err
	}
	var meta model.PartMeta
	if err := json.Unmarshal(metaRaw, &meta); err != nil {
		return model.PartMeta{}, nil, err
	}
	rows, err := readTSV(dataPath, meta.PartID)
	if err != nil {
		return model.PartMeta{}, nil, err
	}
	return meta, rows, nil
}

func readTSV(path, partID string) ([]model.Row, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	if !sc.Scan() {
		return nil, fmt.Errorf("empty tsv")
	}
	header := strings.Split(sc.Text(), "\t")
	idx := map[string]int{}
	for i, h := range header {
		idx[h] = i
	}
	var out []model.Row
	for sc.Scan() {
		cols := strings.Split(sc.Text(), "\t")
		if len(cols) < len(header) {
			continue
		}
		var r model.Row
		r.ID = cols[idx["id"]]
		fmt.Sscanf(cols[idx["ver"]], "%d", &r.Ver)
		r.Value = cols[idx["value"]]
		fmt.Sscanf(cols[idx["expire_ts"]], "%d", &r.ExpireTS)
		r.PartID = partID
		out = append(out, r)
	}
	return out, sc.Err()
}

func ChecksumFile(path string) (string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(raw)
	return "sha256:" + hex.EncodeToString(sum[:]), nil
}

func ListPartDirs(root string) ([]string, error) {
	var dirs []string
	err := filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !d.IsDir() {
			return nil
		}
		if _, err := os.Stat(filepath.Join(path, "part.meta.json")); err == nil {
			dirs = append(dirs, path)
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	sort.Strings(dirs)
	return dirs, nil
}

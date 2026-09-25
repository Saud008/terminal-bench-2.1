package srcursor

import (
	"encoding/json"
	"os"
	"path/filepath"
)

const ReplayPathCursorPath = "/app/state/srcursor-by-path.json"

type ReplayPathCursor struct {
	Resumes map[string][]int `json:"resumes"`
}

func LoadAppliedLines(path, resumePath string) (map[int]struct{}, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return map[int]struct{}{}, nil
		}
		return nil, err
	}
	var led ReplayPathCursor
	if err := json.Unmarshal(raw, &led); err != nil {
		return nil, err
	}
	out := make(map[int]struct{})
	for _, ln := range led.Resumes[resumePath] {
		out[ln] = struct{}{}
	}
	return out, nil
}

func RecordApplied(path, resumePath string, lineNo int) error {
	led := ReplayPathCursor{Resumes: map[string][]int{}}
	raw, err := os.ReadFile(path)
	if err == nil {
		_ = json.Unmarshal(raw, &led)
	}
	if led.Resumes == nil {
		led.Resumes = map[string][]int{}
	}
	for _, ln := range led.Resumes[resumePath] {
		if ln == lineNo {
			return nil
		}
	}
	led.Resumes[resumePath] = append(led.Resumes[resumePath], lineNo)
	out, err := json.MarshalIndent(led, "", "  ")
	if err != nil {
		return err
	}
	out = append(out, '\n')
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, out, 0o644)
}

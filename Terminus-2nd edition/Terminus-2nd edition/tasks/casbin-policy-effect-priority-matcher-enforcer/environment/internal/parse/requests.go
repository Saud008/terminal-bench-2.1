package parse

import (
	"bufio"
	"encoding/json"
	"os"
	"strings"

	"github.com/terminus/casctl/internal/model"
)

func LoadRequests(path string) ([]model.Request, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var out []model.Request
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		var req model.Request
		if err := json.Unmarshal([]byte(line), &req); err != nil {
			return nil, err
		}
		out = append(out, req)
	}
	return out, sc.Err()
}

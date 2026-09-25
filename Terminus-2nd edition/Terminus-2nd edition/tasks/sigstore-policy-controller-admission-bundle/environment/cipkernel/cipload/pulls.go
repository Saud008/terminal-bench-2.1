package cipload

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/terminus/slsacip/cipkernel/ciptypes"
)

// LoadPulls reads a JSONL file of pull admission requests, one Pull object
// per non-blank line, preserving file order.
func LoadPulls(path string) ([]ciptypes.Pull, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open pulls %s: %w", path, err)
	}
	defer f.Close()

	var pulls []ciptypes.Pull
	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 0, 64*1024), 4*1024*1024)

	lineNo := 0
	for scanner.Scan() {
		lineNo++
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		var p ciptypes.Pull
		if err := json.Unmarshal([]byte(line), &p); err != nil {
			return nil, fmt.Errorf("parse pulls %s line %d: %w", path, lineNo, err)
		}
		pulls = append(pulls, p)
	}
	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("scan pulls %s: %w", path, err)
	}
	return pulls, nil
}

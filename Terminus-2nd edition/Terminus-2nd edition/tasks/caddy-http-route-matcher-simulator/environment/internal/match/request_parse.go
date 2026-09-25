package match

import (
	"bufio"
	"bytes"
	"fmt"
	"strings"

	"github.com/terminus/caddyroute/internal/types"
)

// ParseHTTPRequest reads a minimal HTTP/1.1 request from raw bytes.
func ParseHTTPRequest(raw []byte) (types.HTTPRequest, error) {
	scanner := bufio.NewScanner(bytes.NewReader(raw))
	if !scanner.Scan() {
		return types.HTTPRequest{}, fmt.Errorf("empty request")
	}
	parts := strings.Fields(scanner.Text())
	if len(parts) < 2 {
		return types.HTTPRequest{}, fmt.Errorf("bad request line")
	}
	req := types.HTTPRequest{
		Method:  parts[0],
		Path:    parts[1],
		Headers: map[string]string{},
	}
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			break
		}
		idx := strings.Index(line, ":")
		if idx <= 0 {
			continue
		}
		name := strings.TrimSpace(line[:idx])
		val := strings.TrimSpace(line[idx+1:])
		req.Headers[name] = val
	}
	return req, nil
}

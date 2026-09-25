package matcher

import (
	"bufio"
	"bytes"
	"strings"
)

// HTTPRequest is parsed from raw HTTP bytes.
type HTTPRequest struct {
	Method  string
	Path    string
	Headers map[string]string
}

// ParseHTTPRequest reads method line and headers from raw bytes.
func ParseHTTPRequest(data []byte) (*HTTPRequest, error) {
	req := &HTTPRequest{Headers: map[string]string{}}
	scanner := bufio.NewScanner(bytes.NewReader(data))
	if !scanner.Scan() {
		return nil, errBadRequest
	}
	parts := strings.Fields(scanner.Text())
	if len(parts) < 2 {
		return nil, errBadRequest
	}
	req.Method = parts[0]
	req.Path = parts[1]
	for scanner.Scan() {
		line := scanner.Text()
		if line == "" {
			break
		}
		colon := strings.IndexByte(line, ':')
		if colon < 0 {
			continue
		}
		name := strings.TrimSpace(line[:colon])
		val := strings.TrimSpace(line[colon+1:])
		req.Headers[strings.ToLower(name)] = val
	}
	return req, nil
}

var errBadRequest = &parseError{"bad http request"}

type parseError struct{ msg string }

func (e *parseError) Error() string { return e.msg }

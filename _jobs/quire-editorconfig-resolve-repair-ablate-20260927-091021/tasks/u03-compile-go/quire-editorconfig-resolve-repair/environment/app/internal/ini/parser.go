// Package ini reads EditorConfig files with the same line rules as the
// inih-based parser in the C core.
package ini

import (
	"io"
	"os"
	"strings"

	"quire/internal/ctext"
)

// Length limits in bytes. Longer section headers and properties are skipped.
const (
	MaxSectionName   = 4096
	MaxPropertyName  = 1024
	MaxPropertyValue = 4096
)

// Handler receives each property with the section it appeared under; the
// preamble before the first section header has section "".
type Handler func(section, name, value string)

// ParseFile parses the file at path. The error is non-nil only when the file
// could not be opened; a syntax error is reported as a non-zero line number.
func ParseFile(path string, h Handler) (int, error) {
	f, err := os.Open(path)
	if err != nil {
		return 0, err
	}
	defer f.Close()
	return Parse(f, h), nil
}

// Parse calls h for every property in r and returns the number of the first
// line with a syntax error, or 0. Parsing continues after an error.
func Parse(r io.Reader, h Handler) int {
	lr := newLineReader(r)
	section := ""
	errLine := 0
	for lineno := 1; ; lineno++ {
		line, ok := lr.next()
		if !ok {
			break
		}
		if lineno == 1 {
			line = strings.TrimPrefix(line, "\xef\xbb\xbf")
		}
		start := ctext.TrimLeft(ctext.TrimRight(line))
		switch {
		case start == "", start[0] == ';', start[0] == '#':
		case start[0] == '[':
			body := start[1:]
			end := lastIndexBeforeComment(body, ']')
			if end >= len(body) || body[end] != ']' {
				if errLine == 0 {
					errLine = lineno
				}
				continue
			}
			if end > MaxSectionName {
				continue
			}
			section = body[:end]
		default:
			end := indexOrComment(start, '=')
			if end == len(start) || start[end] != '=' {
				end = indexOrComment(start, ':')
			}
			if end == len(start) || (start[end] != '=' && start[end] != ':') {
				if errLine == 0 {
					errLine = lineno
				}
				continue
			}
			name := ctext.TrimRight(start[:end])
			value := ctext.TrimRight(stripComment(ctext.TrimLeft(start[end+1:])))
			if len(name) > MaxPropertyName || len(value) > MaxPropertyValue {
				continue
			}
			h(section, name, value)
		}
	}
	return errLine
}

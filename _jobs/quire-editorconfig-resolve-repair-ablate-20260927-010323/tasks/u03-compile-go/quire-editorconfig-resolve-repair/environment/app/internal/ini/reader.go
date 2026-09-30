package ini

import (
	"bufio"
	"io"
	"strings"
)

// maxLine is the size of the core's line buffer; a physical line longer than
// maxLine-1 bytes is read as several lines.
const maxLine = 5000

type lineReader struct {
	r *bufio.Reader
}

func newLineReader(r io.Reader) *lineReader {
	return &lineReader{r: bufio.NewReader(r)}
}

// next returns the next line including its newline, at most maxLine-1 bytes.
// Anything after a NUL byte is dropped, as the core works on C strings.
func (lr *lineReader) next() (string, bool) {
	buf := make([]byte, 0, 128)
	for len(buf) < maxLine-1 {
		c, err := lr.r.ReadByte()
		if err != nil {
			if len(buf) == 0 {
				return "", false
			}
			break
		}
		buf = append(buf, c)
		if c == '\n' {
			break
		}
	}
	line := string(buf)
	if i := strings.IndexByte(line, 0); i >= 0 {
		line = line[:i]
	}
	return line, true
}

package resolve

import (
	"errors"
	"fmt"
)

var (
	// ErrNotFullPath is returned for a path that does not start with '/'.
	ErrNotFullPath = errors.New("Input file must be a full path name.")
	// ErrVersionTooNew is returned when -b asks for a newer core.
	ErrVersionTooNew = errors.New("Required version is greater than the current version.")
)

// ParseError reports the first line with a syntax error in a file.
type ParseError struct {
	Line int
	File string
}

func (e *ParseError) Error() string {
	return fmt.Sprintf("Failed to parse file.:%d \"%s\"", e.Line, e.File)
}

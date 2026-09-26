package tzif

import (
	"errors"
	"fmt"
)

// ErrNotTZif is returned when the magic number is missing.
var ErrNotTZif = errors.New("tzif: not a TZif file")

func errTruncated(what string) error { return fmt.Errorf("tzif: truncated %s", what) }

func errVersion(v byte) error { return fmt.Errorf("tzif: unsupported version byte %#x", v) }

func errCorrupt(msg string) error { return fmt.Errorf("tzif: corrupt data: %s", msg) }

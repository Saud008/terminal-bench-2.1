// Package diag formats brickmake's own messages the way GNU make does.
package diag

import (
	"fmt"
	"io"
	"os"
)

// Prog is the program name used as the prefix of messages without a
// makefile position.
const Prog = "brickmake"

var (
	Stdout io.Writer = os.Stdout
	Stderr io.Writer = os.Stderr
)

// Pos is a makefile position.
type Pos struct {
	File string
	Line int
}

func (p Pos) Valid() bool { return p.File != "" }

func (p Pos) String() string {
	if !p.Valid() {
		return ""
	}
	return fmt.Sprintf("%s:%d", p.File, p.Line)
}

// Fatal stops the run with exit status 2.
type Fatal struct {
	Pos Pos
	Msg string
}

func (f Fatal) Error() string {
	if f.Pos.Valid() {
		return fmt.Sprintf("%s: *** %s.  Stop.", f.Pos, f.Msg)
	}
	return fmt.Sprintf("%s: *** %s.  Stop.", Prog, f.Msg)
}

// Failf aborts parsing or expansion. It is recovered in main.
func Failf(pos Pos, format string, args ...any) {
	panic(Fatal{Pos: pos, Msg: fmt.Sprintf(format, args...)})
}

// Warn prints "pos: msg" (or "brickmake: msg" without a position) on stderr.
func Warn(pos Pos, format string, args ...any) {
	msg := fmt.Sprintf(format, args...)
	if pos.Valid() {
		fmt.Fprintf(Stderr, "%s: %s\n", pos, msg)
		return
	}
	fmt.Fprintf(Stderr, "%s: %s\n", Prog, msg)
}

// Say prints "brickmake: msg" on stdout.
func Say(format string, args ...any) {
	fmt.Fprintf(Stdout, "%s: %s\n", Prog, fmt.Sprintf(format, args...))
}

// Err prints "brickmake: msg" on stderr.
func Err(format string, args ...any) {
	fmt.Fprintf(Stderr, "%s: %s\n", Prog, fmt.Sprintf(format, args...))
}

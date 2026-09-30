package cli

import (
	"bufio"
	"io"

	"quire/internal/ctext"
)

// input is one file to resolve and whether its name came from stdin.
type input struct {
	name      string
	fromStdin bool
}

// inputs walks the path arguments. A "-" argument stands for every
// non-blank line of stdin, trimmed of surrounding whitespace, until EOF.
type inputs struct {
	args  []string
	stdin *bufio.Reader
	pos   int
}

func newInputs(args []string, stdin io.Reader) *inputs {
	return &inputs{args: args, stdin: bufio.NewReader(stdin)}
}

func (in *inputs) next() (input, bool) {
	for in.pos < len(in.args) {
		arg := in.args[in.pos]
		if arg != "-" {
			in.pos++
			return input{name: arg}, true
		}
		line, err := in.stdin.ReadString('\n')
		if line == "" && err != nil {
			in.pos++
			continue
		}
		name := ctext.TrimLeft(ctext.TrimRight(line))
		if name == "" {
			continue
		}
		return input{name: name, fromStdin: true}, true
	}
	return input{}, false
}

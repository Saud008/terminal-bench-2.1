// Package cli parses the brickmake command line.
package cli

import (
	"fmt"
	"strings"

	"brickmake/internal/parse"
	"brickmake/internal/vars"
)

// Options is a parsed command line.
type Options struct {
	Files      []string
	Dir        string
	DryRun     bool
	Silent     bool
	KeepGoing  bool
	AlwaysMake bool
	Help       bool
	Version    bool
	Assigns    []Assign
	Goals      []string
}

// Assign is a NAME=value (or :=, ::=, +=, ?=) argument.
type Assign struct {
	Name  string
	Op    vars.Op
	Value string
}

var longFlags = map[string]string{
	"--just-print": "n", "--dry-run": "n", "--recon": "n",
	"--silent": "s", "--quiet": "s",
	"--keep-going": "k", "--always-make": "B",
	"--no-builtin-rules": "r", "--no-builtin-variables": "R",
	"--help": "h", "--version": "v",
}

// Parse parses args (without the program name).
func Parse(args []string) (*Options, error) {
	o := &Options{}
	for i := 0; i < len(args); i++ {
		a := args[i]
		if a == "--" {
			for _, rest := range args[i+1:] {
				o.addOperand(rest)
			}
			break
		}
		if strings.HasPrefix(a, "--") {
			name, val, hasVal := strings.Cut(a, "=")
			switch name {
			case "--file", "--makefile", "--directory":
				if !hasVal {
					if i+1 >= len(args) {
						return nil, fmt.Errorf("option '%s' requires an argument", name)
					}
					i++
					val = args[i]
				}
				if name == "--directory" {
					o.Dir = val
				} else {
					o.Files = append(o.Files, val)
				}
				continue
			}
			short, ok := longFlags[a]
			if !ok {
				return nil, fmt.Errorf("unrecognized option '%s'", a)
			}
			o.flag(short[0])
			continue
		}
		if len(a) > 1 && a[0] == '-' {
			for j := 1; j < len(a); j++ {
				c := a[j]
				if c == 'f' || c == 'C' {
					val := a[j+1:]
					if val == "" {
						if i+1 >= len(args) {
							return nil, fmt.Errorf("option requires an argument -- '%c'", c)
						}
						i++
						val = args[i]
					}
					if c == 'f' {
						o.Files = append(o.Files, val)
					} else {
						o.Dir = val
					}
					break
				}
				if !o.flag(c) {
					return nil, fmt.Errorf("invalid option -- '%c'", c)
				}
			}
			continue
		}
		o.addOperand(a)
	}
	return o, nil
}

func (o *Options) flag(c byte) bool {
	switch c {
	case 'n':
		o.DryRun = true
	case 's':
		o.Silent = true
	case 'k':
		o.KeepGoing = true
	case 'B':
		o.AlwaysMake = true
	case 'r', 'R':
	case 'h':
		o.Help = true
	case 'v':
		o.Version = true
	default:
		return false
	}
	return true
}

func (o *Options) addOperand(a string) {
	if name, op, value, ok := parse.ScanAssign(a); ok && name != "" {
		o.Assigns = append(o.Assigns, Assign{Name: name, Op: op, Value: value})
		return
	}
	o.Goals = append(o.Goals, a)
}

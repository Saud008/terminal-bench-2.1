package cli

import (
	"errors"
	"fmt"
	"os"
	"strings"

	"brickmake/internal/db"
	"brickmake/internal/diag"
	"brickmake/internal/engine"
	"brickmake/internal/expand"
	"brickmake/internal/parse"
	"brickmake/internal/text"
	"brickmake/internal/vars"
)

const version = "brickmake 1.4.2"

const usage = `Usage: brickmake [options] [NAME=value ...] [target ...]
Options:
  -f FILE, --file=FILE        Read FILE as the makefile.
  -C DIR, --directory=DIR     Change to DIR before doing anything.
  -n, --just-print            Print recipes instead of running them.
  -s, --silent                Don't echo recipes.
  -k, --keep-going            Keep going when some targets can't be made.
  -B, --always-make           Consider every target out of date.
  -r, -R                      Accepted; builtin rules and variables never exist.
  -h, --help                  Print this message and exit.
  -v, --version               Print the version and exit.
`

var defaultMakefiles = []string{"GNUmakefile", "makefile", "Makefile"}

// Main runs brickmake and returns the exit status.
func Main(args []string) (code int) {
	opts, err := Parse(args)
	if err != nil {
		diag.Err("%s", err)
		fmt.Fprint(diag.Stderr, usage)
		return 2
	}
	if opts.Help {
		fmt.Fprint(diag.Stdout, usage)
		return 0
	}
	if opts.Version {
		fmt.Fprintln(diag.Stdout, version)
		return 0
	}
	if opts.Dir != "" {
		if err := os.Chdir(opts.Dir); err != nil {
			diag.Err("*** %s: %s.  Stop.", opts.Dir, errText(err))
			return 2
		}
		if !opts.Silent {
			wd, _ := os.Getwd()
			diag.Say("Entering directory '%s'", wd)
			defer diag.Say("Leaving directory '%s'", wd)
		}
	}

	global := vars.NewSet()
	x := expand.New(global)
	d := db.New()
	eng := engine.New(d, x)
	eng.DryRun, eng.Silent = opts.DryRun, opts.Silent
	eng.KeepGoing, eng.AlwaysMake = opts.KeepGoing, opts.AlwaysMake
	x.Shell = eng.ShellOutput

	defer func() {
		if r := recover(); r != nil {
			f, ok := r.(diag.Fatal)
			if !ok {
				panic(r)
			}
			fmt.Fprintln(diag.Stderr, f.Error())
			code = 2
		}
	}()

	initVariables(x, opts)
	eng.Env = environment(x, opts)

	files := opts.Files
	if len(files) == 0 {
		for _, name := range defaultMakefiles {
			if _, err := os.Stat(name); err == nil {
				files = []string{name}
				break
			}
		}
	}
	p := parse.New(d, x)
	for _, name := range files {
		src, err := os.ReadFile(name)
		if err != nil {
			diag.Err("%s: %s", name, errText(err))
			diag.Err("*** No rule to make target '%s'.  Stop.", name)
			return 2
		}
		p.Parse(name, src)
	}
	x.Pos = diag.Pos{}

	goals := opts.Goals
	if len(goals) == 0 {
		goals = text.Fields(x.Value(".DEFAULT_GOAL", nil))
		if len(goals) > 1 {
			diag.Failf(diag.Pos{}, "'.DEFAULT_GOAL' contains more than one target")
		}
		if len(goals) == 0 {
			if len(files) == 0 {
				diag.Failf(diag.Pos{}, "No targets specified and no makefile found")
			}
			diag.Failf(diag.Pos{}, "No targets")
		}
	}
	return eng.Run(goals)
}

func errText(err error) string {
	var pe *os.PathError
	if errors.As(err, &pe) {
		err = pe.Err
	}
	s := err.Error()
	if s != "" {
		s = strings.ToUpper(s[:1]) + s[1:]
	}
	return s
}

func initVariables(x *expand.Expander, opts *Options) {
	for _, kv := range os.Environ() {
		name, value, ok := strings.Cut(kv, "=")
		if !ok || name == "" || name == "SHELL" || name == "MAKEFLAGS" || name == "MAKELEVEL" {
			continue
		}
		x.Global.Put(&vars.Var{Name: name, Value: value, Flavor: vars.Recursive, Origin: vars.Environment})
	}
	x.Global.Put(&vars.Var{Name: "SHELL", Value: "/bin/sh", Flavor: vars.Recursive, Origin: vars.Default})
	if wd, err := os.Getwd(); err == nil {
		x.Global.Put(&vars.Var{Name: "CURDIR", Value: wd, Flavor: vars.Simple, Origin: vars.File})
	}
	x.Global.Put(&vars.Var{Name: "MAKECMDGOALS", Value: strings.Join(opts.Goals, " "), Flavor: vars.Recursive, Origin: vars.Default})
	for _, a := range opts.Assigns {
		x.DefineGlobal(a.Name, a.Op, a.Value, vars.CommandLine, diag.Pos{})
	}
}

// environment is the environment of recipes and $(shell): the process
// environment plus the command-line variables.
func environment(x *expand.Expander, opts *Options) []string {
	env := map[string]string{}
	var keys []string
	set := func(k, v string) {
		if _, seen := env[k]; !seen {
			keys = append(keys, k)
		}
		env[k] = v
	}
	for _, kv := range os.Environ() {
		k, v, _ := strings.Cut(kv, "=")
		set(k, v)
	}
	for _, a := range opts.Assigns {
		set(a.Name, x.Value(a.Name, nil))
	}
	set("MAKELEVEL", "1")
	out := make([]string, 0, len(keys))
	for _, k := range keys {
		out = append(out, k+"="+env[k])
	}
	return out
}

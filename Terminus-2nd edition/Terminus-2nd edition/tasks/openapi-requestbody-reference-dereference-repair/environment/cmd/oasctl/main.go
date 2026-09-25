package main

import (
	"fmt"
	"os"

	"github.com/terminus/oasctl/internal/validate"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "validate":
		cfg := flagVal("--config")
		spec := flagVal("--spec")
		payload := flagVal("--payload")
		out := flagVal("--output")
		if cfg == "" || spec == "" || payload == "" || out == "" {
			usage()
			os.Exit(2)
		}
		code, err := validate.Run(cfg, spec, payload, out)
		if err != nil {
			fmt.Fprintf(os.Stderr, "oasctl: %v\n", err)
		}
		os.Exit(code)
	default:
		usage()
		os.Exit(2)
	}
}

func flagVal(name string) string {
	for i, a := range os.Args {
		if a == name && i+1 < len(os.Args) {
			return os.Args[i+1]
		}
	}
	return ""
}

func usage() {
	fmt.Fprintf(os.Stderr, "usage: oasctl validate --spec <path> --payload <dir> --config <path> --output <path>\n")
}

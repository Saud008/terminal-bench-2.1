// Package main provides casctl, the offline access-decision admission CLI for tenant policy bundles.
package main

import (
	"fmt"
	"os"

	"github.com/terminus/casctl/internal/authzkernel"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "enforce":
		cfg := flagVal("--config")
		reqs := flagVal("--requests")
		out := flagVal("--output")
		if cfg == "" || reqs == "" || out == "" {
			usage()
			os.Exit(2)
		}
		code, err := authzkernel.Run(cfg, reqs, out, "/app/fixtures")
		if err != nil {
			fmt.Fprintf(os.Stderr, "casctl: %v\n", err)
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
	fmt.Fprintf(os.Stderr, "usage: casctl enforce --config <path> --requests <path> --output <path>\n")
}

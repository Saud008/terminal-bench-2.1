package main

import (
	"fmt"
	"os"

	"github.com/terminus/dnsplugd/internal/server"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: dnsplugd serve --corefile PATH --listen HOST:PORT")
		os.Exit(2)
	}
	if os.Args[1] != "serve" {
		fmt.Fprintln(os.Stderr, "unknown command")
		os.Exit(2)
	}
	var corefile, listen string
	for i := 2; i < len(os.Args); i++ {
		switch os.Args[i] {
		case "--corefile":
			i++
			corefile = os.Args[i]
		case "--listen":
			i++
			listen = os.Args[i]
		default:
			fmt.Fprintln(os.Stderr, "unknown flag")
			os.Exit(2)
		}
	}
	if corefile == "" || listen == "" {
		fmt.Fprintln(os.Stderr, "missing flags")
		os.Exit(2)
	}
	if err := server.LoadAndServe(listen, corefile); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

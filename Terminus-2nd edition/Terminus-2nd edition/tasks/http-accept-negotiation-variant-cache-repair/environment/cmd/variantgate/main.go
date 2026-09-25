package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/terminus/variantgate/internal/api"
	"github.com/terminus/variantgate/internal/cache"
	"github.com/terminus/variantgate/internal/variants"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "serve":
		fs := flag.NewFlagSet("serve", flag.ExitOnError)
		listen := fs.String("listen", "127.0.0.1:8080", "listen address")
		catalog := fs.String("catalog", "/app/fixtures/catalog.json", "catalog path")
		_ = fs.Parse(os.Args[2:])
		store, err := variants.Load(*catalog)
		if err != nil {
			log.Fatalf("catalog: %v", err)
		}
		srv := api.New(store, cache.New())
		log.Printf("variantgate listening on %s", *listen)
		if err := http.ListenAndServe(*listen, srv.Handler()); err != nil {
			log.Fatal(err)
		}
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: variantgate serve --listen HOST:PORT --catalog PATH")
}

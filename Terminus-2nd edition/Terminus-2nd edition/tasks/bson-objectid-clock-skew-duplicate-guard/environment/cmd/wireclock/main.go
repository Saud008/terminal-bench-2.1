package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/terminus/wireclock/pkg/httpsurf"
	"github.com/terminus/wireclock/pkg/durastore"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "serve":
		fs := flag.NewFlagSet("serve", flag.ExitOnError)
		listen := fs.String("listen", "127.0.0.1:9090", "listen address")
		dbPath := fs.String("db", "/app/data/oidguard.db", "sqlite path")
		_ = fs.Parse(os.Args[2:])
		db, err := durastore.Open(*dbPath)
		if err != nil {
			log.Fatal(err)
		}
		defer db.Close()
		srv := httpsurf.New(db)
		log.Printf("wireclock listening on %s", *listen)
		if err := http.ListenAndServe(*listen, srv.Handler()); err != nil {
			log.Fatal(err)
		}
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: wireclock serve --listen HOST:PORT --db PATH")
}

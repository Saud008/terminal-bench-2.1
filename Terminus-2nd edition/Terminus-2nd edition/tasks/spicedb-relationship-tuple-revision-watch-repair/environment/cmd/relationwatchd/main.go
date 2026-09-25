package main

import (
	"flag"
	"log"
	"net/http"
	"os"

	"github.com/example/spicedb-relation-watch/internal/api"
	"github.com/example/spicedb-relation-watch/internal/config"
	"github.com/example/spicedb-relation-watch/internal/store"
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("usage: relationwatchd serve --config /app/config/relationwatch.json")
	}
	switch os.Args[1] {
	case "serve":
		serveCmd(os.Args[2:])
	default:
		log.Fatalf("unknown command %q", os.Args[1])
	}
}

func serveCmd(args []string) {
	fs := flag.NewFlagSet("serve", flag.ExitOnError)
	cfgPath := fs.String("config", "/app/config/relationwatch.json", "config path")
	_ = fs.Parse(args)

	cfg, err := config.Load(*cfgPath)
	if err != nil {
		log.Fatal(err)
	}
	if err := api.EnsureDirs(cfg); err != nil {
		log.Fatal(err)
	}

	st, err := store.Open(cfg.DBPath)
	if err != nil {
		log.Fatal(err)
	}
	defer st.Close()

	srv := api.New(cfg, st)
	log.Printf("relation watch api on %s", cfg.ListenAddr)
	if err := http.ListenAndServe(cfg.ListenAddr, srv.Handler()); err != nil {
		log.Fatal(err)
	}
}

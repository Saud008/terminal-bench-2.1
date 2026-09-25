package main

import (
	"flag"
	"log"
	"net/http"
	"os"

	"github.com/terminus/party-invite/internal/api"
	"github.com/terminus/party-invite/internal/clock"
	"github.com/terminus/party-invite/internal/config"
	"github.com/terminus/party-invite/internal/store"
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("usage: partyd serve --config /app/config/party.json")
	}
	switch os.Args[1] {
	case "serve":
		serve(os.Args[2:])
	default:
		log.Fatalf("unknown command %q", os.Args[1])
	}
}

func serve(args []string) {
	fs := flag.NewFlagSet("serve", flag.ExitOnError)
	cfgPath := fs.String("config", "/app/config/party.json", "config path")
	_ = fs.Parse(args)

	cfg, err := config.Load(*cfgPath)
	if err != nil {
		log.Fatal(err)
	}
	st, err := store.Open(cfg.DBPath)
	if err != nil {
		log.Fatal(err)
	}
	defer st.Close()

	clk := clock.NewMono()
	srv := api.New(st, cfg, clk)
	log.Printf("partyd listening on %s", cfg.ListenAddr)
	if err := http.ListenAndServe(cfg.ListenAddr, srv.Handler()); err != nil {
		log.Fatal(err)
	}
}

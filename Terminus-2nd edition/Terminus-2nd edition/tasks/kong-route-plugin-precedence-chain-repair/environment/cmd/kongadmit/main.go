package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/terminus/kongadmit/internal/api"
	"github.com/terminus/kongadmit/internal/config"
	"github.com/terminus/kongadmit/internal/export"
	"github.com/terminus/kongadmit/internal/gateway"
	"github.com/terminus/kongadmit/internal/ingest"
	"github.com/terminus/kongadmit/internal/store"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "serve":
		runServe(os.Args[2:])
	case "ingest":
		runIngest(os.Args[2:])
	case "export":
		runExport(os.Args[2:])
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintf(os.Stderr, "usage: kongadmit <serve|ingest|export> [flags]\n")
}

func runServe(args []string) {
	fs := flag.NewFlagSet("serve", flag.ExitOnError)
	cfgPath := fs.String("config", "/app/config/gateway.json", "config path")
	_ = fs.Parse(args)
	cfg, err := config.Load(*cfgPath)
	if err != nil {
		log.Fatal(err)
	}
	st := store.New()
	if _, err := os.Stat(cfg.DeckPath); err == nil {
		deck, err := ingest.LoadDeck(cfg.DeckPath)
		if err != nil {
			log.Fatal(err)
		}
		ingest.Apply(st, deck)
	}
	proxy := &gateway.Proxy{Store: st, UpstreamEcho: cfg.UpstreamEcho}
	admin := &api.Admin{Store: st, DeckPath: cfg.DeckPath}
	go func() {
		log.Printf("proxy listening on %s", cfg.ProxyListen)
		if err := http.ListenAndServe(cfg.ProxyListen, proxy); err != nil {
			log.Fatal(err)
		}
	}()
	go func() {
		log.Printf("admin listening on %s", cfg.AdminListen)
		if err := http.ListenAndServe(cfg.AdminListen, admin); err != nil {
			log.Fatal(err)
		}
	}()
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
}

func runIngest(args []string) {
	fs := flag.NewFlagSet("ingest", flag.ExitOnError)
	deck := fs.String("deck", "", "declarative deck yaml")
	_ = fs.Parse(args)
	if *deck == "" {
		log.Fatal("deck required")
	}
	st := store.New()
	d, err := ingest.LoadDeck(*deck)
	if err != nil {
		log.Fatal(err)
	}
	report := ingest.Apply(st, d)
	enc := json.NewEncoder(os.Stdout)
	_ = enc.Encode(report)
	if !report.OK {
		os.Exit(1)
	}
}

func runExport(args []string) {
	fs := flag.NewFlagSet("export", flag.ExitOnError)
	cfgPath := fs.String("config", "/app/config/gateway.json", "config path")
	_ = fs.Parse(args)
	cfg, err := config.Load(*cfgPath)
	if err != nil {
		log.Fatal(err)
	}
	st := store.New()
	deck, err := ingest.LoadDeck(cfg.DeckPath)
	if err != nil {
		log.Fatal(err)
	}
	report := ingest.Apply(st, deck)
	if !report.OK {
		log.Fatal(report.Errors)
	}
	services, routes, _ := st.Snapshot()
	spec := export.BuildOpenAPI(routes, services)
	enc := json.NewEncoder(os.Stdout)
	_ = enc.Encode(spec)
}

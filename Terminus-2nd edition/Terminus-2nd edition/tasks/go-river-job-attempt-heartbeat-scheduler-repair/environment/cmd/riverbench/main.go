package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/riverbench/internal/api"
	"github.com/terminus/riverbench/internal/config"
	"github.com/terminus/riverbench/internal/store"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "serve":
		runServe(os.Args[2:])
	case "reset":
		runReset(os.Args[2:])
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: riverbench serve|reset [--config PATH]")
}

func runServe(args []string) {
	fs := flag.NewFlagSet("serve", flag.ExitOnError)
	listen := fs.String("listen", "", "listen address")
	cfgPath := fs.String("config", "/app/config/scheduler.json", "config path")
	catalog := fs.String("catalog", "/app/fixtures/seed-catalog.json", "seed catalog")
	_ = fs.Parse(args)

	cfg, err := config.Load(*cfgPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if *listen != "" {
		cfg.Listen = *listen
	}
	st, err := store.Open(cfg.DBPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer st.Close()
	if err := api.ListenAndServe(st, cfg, *catalog); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func runReset(args []string) {
	fs := flag.NewFlagSet("reset", flag.ExitOnError)
	cfgPath := fs.String("config", "/app/config/scheduler.json", "config path")
	_ = fs.Parse(args)
	cfg, err := config.Load(*cfgPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	st, err := store.Open(cfg.DBPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer st.Close()
	if err := st.Reset(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

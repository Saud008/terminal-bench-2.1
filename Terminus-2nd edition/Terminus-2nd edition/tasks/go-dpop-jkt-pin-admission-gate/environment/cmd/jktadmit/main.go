package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/terminus/jktadmit-gate/internal/auditseal"
	"github.com/terminus/jktadmit-gate/internal/gateflow"
	"github.com/terminus/jktadmit-gate/internal/gateway"
	"github.com/terminus/jktadmit-gate/internal/jktpin"
	"github.com/terminus/jktadmit-gate/internal/jtiledger"
	"github.com/terminus/jktadmit-gate/internal/sessionstore"
	"github.com/terminus/jktadmit-gate/internal/settings"
	"github.com/terminus/jktadmit-gate/internal/timepin"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: jktadmit serve --config <path>")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "serve":
		serve(os.Args[2:])
	default:
		fmt.Fprintf(os.Stderr, "unknown command %q\n", os.Args[1])
		os.Exit(2)
	}
}

func serve(args []string) {
	fs := flag.NewFlagSet("serve", flag.ExitOnError)
	cfgPath := fs.String("config", "/app/config/jktadmit.json", "config path")
	_ = fs.Parse(args)

	cfg, err := settings.Load(*cfgPath)
	if err != nil {
		log.Fatalf("config: %v", err)
	}
	if err := cfg.Validate(); err != nil {
		log.Fatalf("config: %v", err)
	}
	vaultKey, err := cfg.VaultKeyBytes()
	if err != nil {
		log.Fatalf("config: %v", err)
	}

	st := sessionstore.New()
	clk := timepin.New()
	pinMgr := &jktpin.Manager{
		Store:      st,
		VaultKey:   vaultKey,
		PinDir:     cfg.PinDir,
		OpenHTU:    cfg.OpenHTU,
		IatSkewSec: cfg.IatSkewSec,
	}
	gate := &gateflow.Gate{
		Store:        st,
		JTILedger:    jtiledger.NewLedger(),
		VaultKey:     vaultKey,
		CheckHTU:     cfg.CheckHTU,
		IatSkewSec:   cfg.IatSkewSec,
		JtiWindowSec: cfg.JtiWindowSec,
	}
	srv := &gateway.Server{
		Store: st,
		Cfg:   cfg,
		Clock: clk,
		Pin:   pinMgr,
		Gate:  gate,
		Seal:  &auditseal.Publisher{},
	}
	httpSrv := &http.Server{Addr: cfg.Listen, Handler: srv.Handler()}

	go func() {
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
		<-sigCh
		_ = httpSrv.Close()
	}()

	log.Printf("jktadmit listening on %s", cfg.Listen)
	if err := httpSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("serve: %v", err)
	}
}

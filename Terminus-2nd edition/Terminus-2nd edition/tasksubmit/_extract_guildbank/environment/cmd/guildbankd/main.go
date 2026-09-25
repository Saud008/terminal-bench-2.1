package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/example/vaultcore/internal/api"
	"github.com/example/vaultcore/internal/clock"
	"github.com/example/vaultcore/internal/config"
	"github.com/example/vaultcore/internal/store"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: guildbankd serve --config /app/config/guildbank.json")
		os.Exit(2)
	}
	if os.Args[1] != "serve" {
		fmt.Fprintln(os.Stderr, "unknown command")
		os.Exit(2)
	}
	fs := flag.NewFlagSet("serve", flag.ExitOnError)
	cfgPath := fs.String("config", "/app/config/guildbank.json", "config path")
	_ = fs.Parse(os.Args[2:])

	cfg, err := config.Load(*cfgPath)
	if err != nil {
		log.Fatal(err)
	}
	st, err := store.Open("/app/work/guildbank.db")
	if err != nil {
		log.Fatal(err)
	}
	defer st.Close()

	clk := clock.NewMono()
	srv := api.New(st, cfg, clk)
	log.Println("guildbankd listening on :8080")
	if err := http.ListenAndServe(":8080", srv.Handler()); err != nil {
		log.Fatal(err)
	}
}

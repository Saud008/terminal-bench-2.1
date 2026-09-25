package main

import (
	"log"
	"net/http"
	"os"

	"github.com/terminus/transit-mock/internal/policy"
	"github.com/terminus/transit-mock/internal/server"
	"github.com/terminus/transit-mock/internal/store"
)

func main() {
	addr := envOr("TRANSIT_LISTEN", "127.0.0.1:8200")
	root := envOr("TRANSIT_ROOT", "/app")
	policyDir := policy.PolicyDir(root)
	srv := &server.Server{Store: store.New(policyDir)}
	log.Printf("transit-mock listening on %s", addr)
	if err := http.ListenAndServe(addr, srv.Handler()); err != nil {
		log.Fatal(err)
	}
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

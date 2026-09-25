package main

import (
	"log"
	"net/http"
	"os"

	"github.com/terminus/paramgate/internal/bind"
	"github.com/terminus/paramgate/internal/config"
	"github.com/terminus/paramgate/internal/openapi"
	"github.com/terminus/paramgate/internal/server"
)

func main() {
	cfgPath := os.Getenv("PARAMGATE_CONFIG")
	if cfgPath == "" {
		cfgPath = "/app/config/paramgate.yaml"
	}
	cfg, err := config.Load(cfgPath)
	if err != nil {
		log.Fatalf("config: %v", err)
	}
	base, err := openapi.LoadFile(cfg.OpenAPI.BaseSpec)
	if err != nil {
		log.Fatalf("base spec: %v", err)
	}
	ext, err := openapi.LoadFile(cfg.OpenAPI.AdminExt)
	if err != nil {
		log.Fatalf("admin spec: %v", err)
	}
	spec := openapi.Merge(base, ext)
	binder := bind.New(spec)
	mux := http.NewServeMux()
	h := &server.Handler{Binder: binder, Routes: buildRoutes(spec)}
	mux.Handle("/v1/", h)
	log.Printf("paramgate listening on %s", cfg.Server.Listen)
	if err := http.ListenAndServe(cfg.Server.Listen, mux); err != nil {
		log.Fatal(err)
	}
}

func buildRoutes(spec openapi.Document) map[string]string {
	routes := map[string]string{}
	for path := range spec.Paths {
		routes[path] = path
	}
	return routes
}

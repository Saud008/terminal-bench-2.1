package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"promingest/internal/server"
)

func main() {
	listen := flag.String("listen", "127.0.0.1:9090", "listen address")
	flag.Parse()
	srv := server.New()
	httpSrv := &http.Server{
		Addr:    *listen,
		Handler: srv.Handler(),
	}
	go func() {
		if err := httpSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal(err)
		}
	}()
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig
	fmt.Println("shutdown")
}

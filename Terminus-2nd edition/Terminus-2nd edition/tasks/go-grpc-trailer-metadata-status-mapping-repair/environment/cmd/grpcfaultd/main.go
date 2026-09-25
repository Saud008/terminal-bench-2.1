package main

import (
	"flag"
	"log"

	"faultserver/internal/fault"
	"faultserver/internal/server"
)

func main() {
	listen := flag.String("listen", "127.0.0.1:50051", "gRPC listen address")
	flag.Parse()

	handler := &fault.Handler{}
	if err := server.ListenAndServe(*listen, handler); err != nil {
		log.Fatal(err)
	}
}

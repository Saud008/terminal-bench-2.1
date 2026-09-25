package server

import (
	"fmt"
	"net"

	faultv1 "faultserver/api/faultv1"
	"faultserver/internal/fault"
	"faultserver/internal/grpc/interceptors"

	"google.golang.org/grpc"
	"google.golang.org/grpc/health"
	healthpb "google.golang.org/grpc/health/grpc_health_v1"
	"google.golang.org/grpc/reflection"
)

func New(handler *fault.Handler) *grpc.Server {
	s := grpc.NewServer(interceptors.UnaryChain(), interceptors.StreamChain())
	faultv1.RegisterAdminServer(s, handler)
	faultv1.RegisterInjectServer(s, handler)
	healthServer := health.NewServer()
	healthServer.SetServingStatus("", healthpb.HealthCheckResponse_SERVING)
	healthpb.RegisterHealthServer(s, healthServer)
	reflection.Register(s)
	return s
}

func ListenAndServe(addr string, handler *fault.Handler) error {
	lis, err := net.Listen("tcp", addr)
	if err != nil {
		return fmt.Errorf("listen: %w", err)
	}
	s := New(handler)
	return s.Serve(lis)
}

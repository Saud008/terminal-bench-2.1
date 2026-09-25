package interceptors

import (
	"context"
	"strings"

	faultgrpc "faultserver/internal/grpc"
	faultv1 "faultserver/api/faultv1"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

func RecvLimitUnary() grpc.UnaryServerInterceptor {
	return func(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error) {
		if !strings.HasPrefix(info.FullMethod, "/fault.v1.Inject/") {
			return handler(ctx, req)
		}
		size := messageSize(req)
		if size > faultgrpc.MaxUserMessageBytes {
			return nil, status.Error(codes.ResourceExhausted, "recv limit exceeded")
		}
		return handler(ctx, req)
	}
}

func messageSize(req any) int {
	if inject, ok := req.(*faultv1.InjectRequest); ok {
		return len(inject.GetPayload())
	}
	return 0
}

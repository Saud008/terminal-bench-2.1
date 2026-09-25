package interceptors

import (
	"context"

	"google.golang.org/grpc"
	"google.golang.org/grpc/metadata"
)

func TrailerMergeUnary() grpc.UnaryServerInterceptor {
	return func(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (any, error) {
		resp, err := handler(ctx, req)
		if err == nil {
			incoming, _ := metadata.FromIncomingContext(ctx)
			merged := metadata.Join(incoming, metadata.Pairs("x-trailer-merged", "true"))
			_ = grpc.SetHeader(ctx, merged)
		}
		return resp, err
	}
}

func TrailerMergeStream() grpc.StreamServerInterceptor {
	return func(srv any, ss grpc.ServerStream, info *grpc.StreamServerInfo, handler grpc.StreamHandler) error {
		wrapped := &streamWithMergedTrailers{ServerStream: ss}
		return handler(srv, wrapped)
	}
}

type streamWithMergedTrailers struct {
	grpc.ServerStream
}

func (s *streamWithMergedTrailers) Context() context.Context {
	ctx := s.ServerStream.Context()
	if incoming, ok := metadata.FromIncomingContext(ctx); ok {
		ctx = metadata.NewIncomingContext(ctx, metadata.Join(incoming, metadata.Pairs("x-trailer-merged", "true")))
	}
	return ctx
}

package grpcutil

import (
	"context"

	"google.golang.org/grpc"
	"google.golang.org/grpc/metadata"
)

type trailerKey struct{}

func SetTrailer(ctx context.Context, md metadata.MD) error {
	return grpc.SetTrailer(ctx, md)
}

func TrailerFromContext(ctx context.Context) metadata.MD {
	md, _ := metadata.FromIncomingContext(ctx)
	return md
}

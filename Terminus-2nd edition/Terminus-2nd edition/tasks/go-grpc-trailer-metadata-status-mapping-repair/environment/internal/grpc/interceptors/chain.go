package interceptors

import "google.golang.org/grpc"

func UnaryChain() grpc.ServerOption {
	return grpc.ChainUnaryInterceptor(RecvLimitUnary(), TrailerMergeUnary())
}

func StreamChain() grpc.ServerOption {
	return grpc.ChainStreamInterceptor(TrailerMergeStream())
}

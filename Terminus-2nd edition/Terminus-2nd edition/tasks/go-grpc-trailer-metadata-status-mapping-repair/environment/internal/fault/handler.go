package fault

import (
	"context"
	"fmt"

	faultv1 "faultserver/api/faultv1"
	faultgrpc "faultserver/internal/grpc"
	"faultserver/internal/grpcutil"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
)

type Handler struct {
	faultv1.UnimplementedAdminServer
	faultv1.UnimplementedInjectServer
	Catalog Catalog
}

func (h *Handler) ConfigureCatalog(_ context.Context, req *faultv1.ConfigureCatalogRequest) (*faultv1.ConfigureCatalogResponse, error) {
	if req.GetSeed() == "" {
		return nil, faultgrpc.Errorf(codes.InvalidArgument, "seed required")
	}
	h.Catalog = Configure(req.GetSeed())
	return &faultv1.ConfigureCatalogResponse{CaseCount: int32(len(h.Catalog.Cases))}, nil
}

func (h *Handler) UnaryInject(ctx context.Context, req *faultv1.InjectRequest) (*faultv1.InjectResponse, error) {
	switch req.GetCaseId() {
	case "trailer-split":
		_ = grpcutil.SetTrailer(ctx, metadata.Pairs(h.Catalog.TrailerKey, "tail-only", "x-shared", "from-trailer"))
		return &faultv1.InjectResponse{Echo: "trailer-split"}, nil
	case "status-details":
		return nil, faultgrpc.WithDetailInfo(codes.FailedPrecondition, "precondition failed", h.Catalog.DetailKey, "seed="+h.Catalog.Seed)
	case "ctx-cancel":
		return nil, faultgrpc.FromContextErr(context.Canceled)
	case "recv-limit-body":
		if len(req.GetPayload()) > faultgrpc.MaxUserMessageBytes {
			return nil, faultgrpc.Errorf(codes.ResourceExhausted, "message too large")
		}
		return &faultv1.InjectResponse{Echo: fmt.Sprintf("bytes=%d", len(req.GetPayload()))}, nil
	case "unary-shape":
		return nil, faultgrpc.ShapeUnary(codes.InvalidArgument, "unary invalid argument")
	default:
		return nil, faultgrpc.Errorf(codes.NotFound, "unknown case %s", req.GetCaseId())
	}
}

func (h *Handler) ServerStream(req *faultv1.InjectRequest, stream faultv1.Inject_ServerStreamServer) error {
	switch req.GetCaseId() {
	case "stream-shape":
		return faultgrpc.ShapeStream(codes.InvalidArgument, "stream invalid argument")
	case "trailer-split":
		_ = grpcutil.SetTrailer(stream.Context(), metadata.Pairs(h.Catalog.TrailerKey, "stream-tail"))
		return stream.Send(&faultv1.InjectResponse{Echo: "stream-trailer"})
	default:
		count := req.GetStreamCount()
		if count <= 0 {
			count = 2
		}
		for i := int32(0); i < count; i++ {
			if err := stream.Send(&faultv1.InjectResponse{Echo: fmt.Sprintf("chunk-%d", i)}); err != nil {
				return err
			}
		}
		return nil
	}
}

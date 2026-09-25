package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"time"

	faultv1 "faultserver/api/faultv1"
	faultgrpc "faultserver/internal/grpc"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
)

type probeResult struct {
	Code         string            `json:"code"`
	Message      string            `json:"message"`
	Headers      map[string]string `json:"headers"`
	Trailers     map[string]string `json:"trailers"`
	DetailReason string            `json:"detail_reason"`
}

func main() {
	addr := flag.String("addr", "127.0.0.1:50051", "server address")
	seed := flag.String("seed", "", "catalog seed")
	caseID := flag.String("case", "", "fault case id")
	mode := flag.String("mode", "unary", "unary or stream")
	payloadSize := flag.Int("payload-size", 0, "payload bytes for recv-limit probes")
	flag.Parse()

	if *seed == "" || *caseID == "" {
		fmt.Fprintln(os.Stderr, "seed and case required")
		os.Exit(2)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	conn, err := grpc.NewClient(*addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		fail(err)
	}
	defer conn.Close()

	admin := faultv1.NewAdminClient(conn)
	if _, err := admin.ConfigureCatalog(ctx, &faultv1.ConfigureCatalogRequest{Seed: *seed}); err != nil {
		fail(err)
	}

	inject := faultv1.NewInjectClient(conn)
	var headerMD metadata.MD
	var trailerMD metadata.MD
	callCtx := metadata.AppendToOutgoingContext(ctx, "x-shared", "from-header", "x-heavy-meta", "abcdefghijklmnopqrstuvwxyz0123456789abcdef")

	switch *mode {
	case "unary":
		req := &faultv1.InjectRequest{CaseId: *caseID, Payload: makePayload(*payloadSize)}
		_, err = inject.UnaryInject(callCtx, req, grpc.Header(&headerMD), grpc.Trailer(&trailerMD))
	default:
		stream, serr := inject.ServerStream(callCtx, &faultv1.InjectRequest{CaseId: *caseID, StreamCount: 1}, grpc.Header(&headerMD), grpc.Trailer(&trailerMD))
		if serr != nil {
			err = serr
			break
		}
		for {
			_, recvErr := stream.Recv()
			if recvErr == io.EOF {
				err = nil
				break
			}
			if recvErr != nil {
				err = recvErr
				break
			}
		}
	}

	out := probeResult{
		Code:         status.Code(err).String(),
		Message:      status.Convert(err).Message(),
		Headers:      mdMap(headerMD),
		Trailers:     mdMap(trailerMD),
		DetailReason: faultgrpc.DetailReason(err),
	}
	if err == nil {
		out.Code = "OK"
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	_ = enc.Encode(out)
}

func makePayload(n int) []byte {
	if n <= 0 {
		return nil
	}
	out := make([]byte, n)
	for i := range out {
		out[i] = byte('a' + (i % 26))
	}
	return out
}

func mdMap(md metadata.MD) map[string]string {
	out := map[string]string{}
	for key, vals := range md {
		if len(vals) > 0 {
			out[key] = vals[0]
		}
	}
	return out
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}

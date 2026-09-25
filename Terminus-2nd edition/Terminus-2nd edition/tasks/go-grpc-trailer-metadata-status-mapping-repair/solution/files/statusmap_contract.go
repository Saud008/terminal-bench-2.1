package faultgrpc

import (
	"context"
	"errors"
	"fmt"

	"google.golang.org/genproto/googleapis/rpc/errdetails"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

const MaxUserMessageBytes = 48

func Errorf(code codes.Code, format string, args ...any) error {
	return status.Errorf(code, format, args...)
}

func FromContextErr(err error) error {
	if err == nil {
		return nil
	}
	if errors.Is(err, context.Canceled) {
		return status.Error(codes.Canceled, "context canceled")
	}
	if errors.Is(err, context.DeadlineExceeded) {
		return status.Error(codes.DeadlineExceeded, err.Error())
	}
	return status.Convert(err).Err()
}

func WithDetailInfo(code codes.Code, message, reason, domain string) error {
	st := status.New(code, message)
	detail := &errdetails.ErrorInfo{Reason: reason, Domain: domain}
	withDetails, err := st.WithDetails(detail)
	if err != nil {
		return st.Err()
	}
	return withDetails.Err()
}

func ShapeUnary(code codes.Code, message string) error {
	return status.Error(code, message)
}

func ShapeStream(code codes.Code, message string) error {
	return status.Error(code, message)
}

func Code(err error) codes.Code {
	if err == nil {
		return codes.OK
	}
	return status.Code(err)
}

func DetailReason(err error) string {
	if err == nil {
		return ""
	}
	st, ok := status.FromError(err)
	if !ok {
		return ""
	}
	for _, detail := range st.Details() {
		if info, ok := detail.(*errdetails.ErrorInfo); ok {
			return info.GetReason()
		}
	}
	return ""
}

func Message(err error) string {
	if err == nil {
		return ""
	}
	return status.Convert(err).Message()
}

func Format(code codes.Code, msg string) string {
	return fmt.Sprintf("%s:%s", code.String(), msg)
}

.PHONY: build test vet zones

build:
	go build -o shiftclock ./cmd/shiftclock

test:
	go test ./...

vet:
	go vet ./...

zones:
	scripts/refresh-zones.sh $(shell cat zones/VERSION)

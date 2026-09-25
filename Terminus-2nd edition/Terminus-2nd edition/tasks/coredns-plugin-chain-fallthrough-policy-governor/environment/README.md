Mini CoreDNS-style plugin chain DNS server for Terminus.

Runtime image uses the Terminal-Bench canonical Go base: `public.ecr.aws/docker/library/golang:1.24-bookworm` (digest-pinned, `linux/amd64`). Agents extend Go sources under `/app` and rebuild `dnsplugd`; the verifier rebuilds before behavioral checks.

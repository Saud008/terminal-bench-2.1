#!/usr/bin/env bash
set -euo pipefail
sed -i 's/gen.ApqAuditSeq = gen.ApqAuditSeq$/gen.ApqAuditSeq = gen.ApqAuditSeq + 1/' \
  /app/internal/ledgerreconcile/run.go
sed -i 's/active := len(ops)/active := countStatus(ops, "active")/' /app/internal/ledgerreconcile/run.go
sed -i 's/evicted := 0/evicted := countStatus(ops, "evicted")/' /app/internal/ledgerreconcile/run.go
grep -q 'countStatus(ops, "active")' /app/internal/ledgerreconcile/run.go
grep -q 'ApqAuditSeq + 1' /app/internal/ledgerreconcile/run.go || grep -q 'ApqAuditSeq = gen.ApqAuditSeq + 1' /app/internal/ledgerreconcile/run.go
test -f /app/internal/ledgerreconcile/run.go

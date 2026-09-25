# Decoy yardsummary contract

The yardsummary decoy module under /app/internal/decoy/yardsummary is informational only.

## Isolation

yardsummary must not read staged_dwell, must not influence run-dwell-ledger math, and must not alter publish-invoices output.

## Purpose

Decoy summaries may count containers, holds, and closures for operator dashboards. Publish hot path uses holdpolicy, pauseclock, closurecal, tarifftier, and invoicewriter only.

## Verification

Pytest confirms invoice and staging digests match reference math without invoking yardsummary on the publish path.

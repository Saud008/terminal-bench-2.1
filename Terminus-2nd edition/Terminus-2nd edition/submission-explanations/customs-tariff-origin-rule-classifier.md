# Submission explanations — customs-tariff-origin-rule-classifier

**Task folder:** tasks/customs-tariff-origin-rule-classifier/
**Platform form only** — not in upload zip.
**Updated:** 2026-07-09T13:50:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Customs brokers must classify shipment lines under trade agreements using HS10 codes, bill-of-materials shares, and certificate validity windows. The work spans parse, score, and atlas stages with a SQLite ledger and workbench JSON buffers. Bugs interact across codify padding, concession share math, credential dates, agreement ranking, and classout emission gates. A fix on one manifest can still fail on expiry edges, regional value floors, or precedence ties. Hidden manifests and cross-stage gates block one-file shortcuts.

## Solution Explanation

The oracle copies five corrected Go modules into codify, concession, and classout packages, then rebuilds originctl. Each patch aligns one contract layer with the docs for HS padding, regional value, certificates, rule ranking, and atlas output. The main insight is that write-atlas must run only after parse and score stages populate the ledger and workbench files. Rebuild is required because the verifier always compiles fresh binaries.

## Verification Explanation

test.sh rebuilds originctl before pytest runs. Tests invoke the CLI through subprocess and compare JSON to independent reference math in tariff_ref.py. Bundled manifests cover HS padding, RVC floors, certificate windows, and agreement precedence. Hidden fixture directories exercise traps that bundled data alone would not catch. NOP on the broken baseline should fail most behavioral checks while oracle plus rebuild should pass all twenty-nine tests.

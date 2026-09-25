# invoice-publish-contract.md

publish-invoices requires reconcile_pass > 0 in reconcile-pass.json. Output subscription-invoices.json includes reconcile_pass echoing the pass counter (1 after the first successful reconcile on a fresh workspace). Invoice_lines sorted by line_kind, segment_index. ledger_digest sha256 of invoice_lines compact JSON.

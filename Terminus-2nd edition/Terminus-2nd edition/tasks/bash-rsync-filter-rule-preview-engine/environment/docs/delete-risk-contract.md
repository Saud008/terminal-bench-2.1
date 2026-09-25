# Delete risk contract

Preview evaluates the sorted union of sender inventory paths and receiver manifest paths.

Delete risk scans the stacked rule chain for P and R token matches independent of transfer first-match. Any path matching a P rule receives delete_risk protected when present on the receiver. Receiver-only paths matching R receive delete_risk candidate. Other receiver-only paths with transfer exclude receive delete_risk candidate unless a P rule matched.

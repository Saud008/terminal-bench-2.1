# Engineering problem contract — go-vault-token-lease-renewal-risk-auditor

Task identity: `702cfb434a`

Renewal admission is stateful in two directions. A row depends on earlier renewals of the same token through lifetime budget fields, and on renewals of other tokens through parent delegation. Neither dependency is visible from a single transcript line.

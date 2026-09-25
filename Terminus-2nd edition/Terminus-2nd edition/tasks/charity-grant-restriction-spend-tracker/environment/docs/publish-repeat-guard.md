# publish repeat guard

Repeated publish-spend-atlas calls in the same amendment pass must not double aggregate spent_cents in grant_balances. published_spend is audit metadata only and must not change atlas totals on rerun.

# amendment pass rules

apply-amendments recomputes staged_balances and staged_rejections from SQLite rows loaded earlier. It does not accept --scenario; the active portfolio is the one already written by load-portfolio into /app/state/grant-portfolio.db. amendment_pass in /app/state/amendment-pass.json increments once per successful apply call. Amendment pass never mutates raw expense rows.

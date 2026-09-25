# Export positions (JSON)

Default output path: /app/output/positions.json

```json
{
  "version": 1,
  "positions": [
    {
      "symbol": "AAPL",
      "net_qty": 200,
      "vwap": "151.250000",
      "fill_count": 3
    }
  ]
}
```

## Field rules

- `positions` sorted by `symbol` ascending.
- Only **trade** execution reports affect quantity and VWAP: tag `35=8` with `150` in `1` (partial), `2` (fill), or `F` (trade).
- `Side` tag `54`: `1` = buy (positive qty), `2` = sell (negative qty).
- `net_qty` uses signed quantity from `LastQty` (tag 32) for trades.
- **Cancel** reports (`150=4`) reduce open interest: subtract signed quantity using tag `38` (`OrderQty` of the canceled remainder). A buy cancel subtracts from net long; a sell cancel adds back (reduces short).
- `vwap` is volume-weighted average price across trade fills for the symbol: `sum(last_px * last_qty) / sum(last_qty)` using tag `31` and `32`. Use six digits after the decimal point. When there are no trade fills, omit the symbol or set `vwap` to `"0.000000"`.
- `fill_count` counts distinct trade execution rows for the symbol after idempotent deduplication.

Use chained VWAP across all trade fills in replay order, not the last trade price alone.

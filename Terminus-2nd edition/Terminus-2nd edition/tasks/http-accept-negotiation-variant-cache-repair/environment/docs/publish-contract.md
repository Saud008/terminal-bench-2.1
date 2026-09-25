# Publish contract

Stage 2 of negotiation reads `/app/state/negotiation.snapshot.json` and chooses a catalog variant.

## Inputs

- `snap.Prepared` — prepared Accept-family header strings
- `variants` — catalog variant list for the staged resource id

## Ranking

Parse each prepared header with `negotiate.ParseList`, then rank with `negotiate.RankEntries`. Drop entries with `q=0`. Sort by `q` descending; when `q` ties, preserve original header list order (earlier entries rank higher). Use stable sorting.

Compare scored candidates with `negotiate.BetterCandidate` when more than one variant remains eligible.

## Charset gate

When `prepared.Accept-Charset` is empty, skip charset filtering and score with Accept q × Accept-Language q only.

When `Accept-Charset` was sent, require a matching charset entry for each candidate variant and multiply Accept q × Accept-Language q × Accept-Charset q.

## Winner selection

Among eligible variants, pick the highest score. Tie-break in order:

1. earlier matching Accept entry position
2. higher media type specificity (exact beats `type/*` beats `*/*`)
3. higher language exactness (exact tag beats prefix-only match)
4. earlier variant index in the catalog list

When no variant qualifies, return no match so the handler can emit `406 Not Acceptable`.

## Output

Return the chosen variant media type, charset, language, and body bytes. The HTTP layer sets `Content-Type`, `Vary`, and `X-Cache`.

See `/app/docs/negotiation-snapshot.md` for staging file layout and `/app/docs/cache-contract.md` for response caching.

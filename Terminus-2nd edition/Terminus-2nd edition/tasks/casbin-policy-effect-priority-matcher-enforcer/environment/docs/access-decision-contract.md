# Access-decision authenticity contract

Trust contract for casctl offline access-decision admission. `casctl enforce` loads a model, merges configured policy bundles, and evaluates access-request batches under the trust model in `/app/docs/trust-admission-workflow.md`.

## Policy effect

Deny-overrides-allow: collect all rule hits (multiple rules at the same priority each count separately), then:

- If any matched policy has `eft=deny` → decision `deny`
- Else if any matched policy has `eft=allow` → decision `allow`
- Else → decision `deny`

## Priority

Policy rules sort by `priority` ascending (lower number = higher precedence) before matching. Effect still considers every match.

## Rule binding

Per model rule binding:

`g(r.sub, p.sub, r.dom) && r.dom == p.dom && keyMatch(r.obj, p.obj) && keyMatch(r.act, p.act)`

- `keyMatch`: exact match or policy field `*` for object and action
- Request action is matched against the policy action field
- Request object is matched against the policy object field

## Role inheritance

`g` grouping is domain-scoped and transitive: if `a→b` and `b→c` in domain `d`, subject `a` inherits role `c` in `d`.

## Domain filter

Only policies where `p.dom == r.dom` may match a request.

## Bundle merge

Config `bundles` lists candidate bundle directory names under `/app/fixtures/policies/` in config order. Config `seed` deterministically selects which candidates load and in what merge order. Export `bundles` and snapshot `bundles` list the same selected subset in the same shuffled order.

Let `digest` be the 32-byte SHA-256 hash of the seed string encoded as UTF-8.

### Seed subset selection

- `bits = digest[0] | (digest[1] << 8)` (16-bit unsigned integer).
- Include the bundle at config index `i` (0-based) when `(bits >> i) & 1 == 1`.
- If no bundle is selected, include exactly one bundle: `bundles[digest[2] % len(bundles)]`.

### Shuffled merge order

Apply Fisher–Yates to the selected subset using `digest` bytes as the shuffle source (not `math/rand` or a separate PRNG):

- Copy the selected bundle names into `out`.
- For `i` from `len(out) - 1` down to `1`:
  - `j = digest[i % len(digest)] % (i + 1)`
  - swap `out[i]` and `out[j]`.
- Append policies and groupings from each bundle in final `out` order.

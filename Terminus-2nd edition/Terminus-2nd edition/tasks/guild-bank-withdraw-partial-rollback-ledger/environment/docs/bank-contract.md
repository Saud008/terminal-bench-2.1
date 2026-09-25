# Guild bank HTTP contract

Base URL: `http://127.0.0.1:8080`

Optional header `X-Test-Mono-Ms` pins the monotonic clock (int64 milliseconds).

## POST /v1/guild/bootstrap

```json
{ "guild_id": "string", "initial_gold": 10000, "interest_rate_bps": 250 }
```

- `guild_id` and `initial_gold` required.
- `interest_rate_bps` optional; default from the service manifest at /app/config/guildbank.json.

Response `200`:

```json
{ "guild_id": "string", "gold_balance": 10000, "interest_rate_bps": 250 }
```

## POST /v1/guild/{guildId}/deposit/stack

```json
{ "item_template_id": "string", "quantity": 40, "bound": false }
```

Response `200` includes `stack_id`, `item_template_id`, `quantity`, `bound`.

## POST /v1/guild/{guildId}/withdraw/gold

```json
{ "player_id": "string", "amount": 500 }
```

- **409** when `amount` exceeds treasury balance.

Response `200` includes `gold_balance` after a successful withdraw.

## POST /v1/guild/{guildId}/withdraw/stack

```json
{ "player_id": "string", "stack_id": "string", "quantity": 10 }
```

- **409** when quantity exceeds stack size or stack is unknown.
- Stack withdraw updates vault and slice rows as described in `/app/docs/stack-split.md`.

## POST /v1/guild/{guildId}/transfer-out

```json
{ "player_id": "string", "stack_id": "string" }
```

- Moves the entire vault stack to `player_stacks` when unbound.
- Bound stacks return **409**; see `/app/docs/bound-items.md`.

## POST /v1/admin/interest/run

```json
{ "guild_id": "string", "period_id": "string" }
```

Accrues one interest period. Field meanings in `/app/docs/interest-journal.md`.

## POST /v1/admin/interest/replay

```json
{ "guild_id": "string", "period_id": "string" }
```

Completes or re-reads a journal period without double-crediting; see `/app/docs/interest-journal.md`.

## POST /v1/guild/export

```json
{ "guild_id": "string" }
```

Writes `/app/output/guild-audit.json` using `/app/docs/export-schema.md`.

# Roster format

Roster JSON:

```json
{
  "rounds": <u32>,
  "actors": [ { ...Actor } ]
}
```

Actor fields: `id`, `name`, `initiative`, `hp`, `max_hp`, `bleed`, `action_points`, optional `stunned`, `pinned`, `alive` (default true).

Scenarios in `/app/fixtures/catalog.json` point to files under `/app/fixtures/rosters/`.

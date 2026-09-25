# Declarative deck schema

Deck YAML top-level keys: `services`, `routes`, `consumers`.

## Service

- `name` (string, required)
- `url` (string, required)
- `plugins` (list, optional)

## Route

- `name`, `service`, `paths` (list), `methods` (list)
- `scope_tags` — JWT scope requirements (authorization)
- `tags` — metadata only (metrics, documentation); **not** used for JWT scope checks
- `plugins` (list, optional)

## Consumer

- `username`
- `jwt.key` — bearer token value
- `jwt.scopes` — granted scope strings

Bundled reference deck: `/app/fixtures/deck-bundled.yaml`.

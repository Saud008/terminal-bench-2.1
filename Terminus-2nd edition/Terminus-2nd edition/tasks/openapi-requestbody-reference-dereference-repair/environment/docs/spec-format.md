# OpenAPI spec format

The bundled spec is OpenAPI 3.0 YAML at `/app/fixtures/openapi.yaml`. Operations use `METHOD /path` keys (for example `POST /pets`). Request bodies live under `paths.*.*.requestBody.content.application/json.schema`.

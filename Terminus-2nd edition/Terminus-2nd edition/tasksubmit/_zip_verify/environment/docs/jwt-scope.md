# JWT scope authorization

The `jwt` plugin validates `Authorization: Bearer <consumer.jwt.key>`.

Scope enforcement compares the consumer's `jwt.scopes` against the route's **`scope_tags`** field. Every `scope_tags` entry must be present in the consumer scopes.

The route `tags` field is for metrics/documentation only and must not satisfy or substitute for `scope_tags` during authorization.

Missing `Authorization` → 401 `missing authorization`. Unknown key → 401 `unknown consumer`. Missing required scope → 401 `insufficient scope`.

Routes with an empty `scope_tags` list allow any authenticated consumer.

# Fixture catalog

| Stack | Focus |
|-------|--------|
| `/app/fixtures/stacks/001-basic-login.json` | auth → account → session with env in account |
| `/app/fixtures/stacks/002-requisite-halt.json` | requisite failure short-circuits auth phase |
| `/app/fixtures/stacks/003-required-continue.json` | required failure still runs later auth modules |
| `/app/fixtures/stacks/004-sufficient-skip.json` | sufficient success skips remaining auth modules |
| `/app/fixtures/stacks/005-include-flat.json` | single-level include fragment |
| `/app/fixtures/stacks/006-include-nested.json` | nested includes within depth limit |
| `/app/fixtures/stacks/007-env-gated.json` | pam_env during auth commits only after auth ok |
| `/app/fixtures/stacks/008-audit-rollback.json` | rollback env before audit on account failure |
| `/app/fixtures/stacks/009-phase-gate.json` | auth failure skips account env commit |
| `/app/fixtures/stacks/010-password-gate.json` | password failure skips session phase |
| `/app/fixtures/stacks/011-sufficient-after-fail.json` | sufficient success cannot override earlier required failure |
| `/app/fixtures/stacks/012-deep-include.json` | five-level include chain within depth limit |
| `/app/fixtures/stacks/013-auth-multi-env.json` | all auth-phase pam_env keys commit after successful auth |
| `/app/fixtures/stacks/014-optional-fail.json` | optional module failure ignored when later required module succeeds |
| `/app/fixtures/stacks/015-account-env-immediate.json` | account-phase pam_env commits immediately (not auth pending) |
| `/app/fixtures/stacks/016-include-sequence.json` | sibling includes expand inline preserving fragment order |
| `/app/fixtures/stacks/017-depth-eight.json` | eight include frames (depth limit boundary) |
| `/app/fixtures/stacks/018-depth-overflow.json` | parse-only fixture exceeding include depth limit (exit `2`) |
| `/app/fixtures/stacks/019-requisite-account-halt.json` | requisite failure short-circuits account phase and skips session |
| `/app/fixtures/stacks/020-include-auth-module-order.json` | sibling includes preserve auth-phase module order (sufficient before required) |

```text
pamreplay replay --stack /app/fixtures/stacks/<file>.json \
  --user alice --export /app/output/<file>.json
```

Integrity digests are recorded in `/app/fixtures/manifest.json` at image build time.

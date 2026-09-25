# Fixture catalog

Bundled playbooks:

| Playbook | Focus |
|----------|-------|
| `m1-inventory.yml` | Inventory group/host layering only |
| `m2-roles.yml` | Inventory plus nginx and app role defaults/vars |
| `m3-merge.yml` | Full stack with hash merge, include_vars depth, playbook and extra vars |

Bundled inventory hosts: `web01`, `web02`, `edge01`.

Role names: `nginx`, `app`.

The nginx role default `worker_pool: 2` collides with inventory `worker_pool` on web hosts so tests can verify inventory overrides defaults before role vars apply.

Include var files live under `/app/vars/` and are referenced relative to each playbook directory. The full-stack playbook also supports an optional extra-vars file under `/app/vars/`.

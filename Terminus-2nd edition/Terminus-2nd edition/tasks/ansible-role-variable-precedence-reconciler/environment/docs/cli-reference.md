# CLI reference

## resolve

```text
ansible-var-merge resolve \
  --playbook /app/playbooks/m1-inventory.yml \
  --inventory /app/inventory \
  --host web01 \
  --seed alpha01 \
  [--extra-vars /app/vars/extra-hotfix.yml] \
  --out /app/output/resolve.json
```

Exit code `0` on success. stdout is not used; the JSON document is written to `--out`.

Required flags: `--playbook`, `--inventory`, `--host`, `--seed`. `--out` defaults to `/app/output/resolve.json`.

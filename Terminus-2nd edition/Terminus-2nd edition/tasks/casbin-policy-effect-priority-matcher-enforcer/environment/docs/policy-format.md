# Policy bundle format

Policy CSV bundles for offline access-decision admission. Each bundle directory under `/app/fixtures/policies/<bundle>/` contains:

| File | Content |
|------|---------|
| `p.csv` | Policy rules: `priority,sub,dom,obj,act,eft` |
| `g.csv` | Grouping: `child,parent,dom` |

`eft` is `allow` or `deny`. Subject values prefixed `role:` are role tokens for matcher `g()`.

CSV files include a header row.

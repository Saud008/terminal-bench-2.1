# Delivery flags

## h (headers only)

When `h` is present on a recipe, condition regexes apply only to the header section (text before the first blank line).

## c (continue)

When `c` is present and the recipe delivers, evaluation continues with the next sibling recipe at the same block level. Without `c`, a successful delivery stops further siblings at that level for the message.

## Combined h and c

When both flags are set on one recipe:

- Condition matching uses headers only (`h`), same as `h` alone.
- After a successful delivery from that recipe, sibling recipes at the same block level are still evaluated (`c`), same as `c` alone.

`pipeline.sh` calls `deliver_record` **once** per successful recipe delivery (one call per matching recipe that has a mbox target). The `c` flag does **not** mean calling `deliver_record` a second time for the same recipe row. Continue means evaluating **later sibling recipes**, not delivering twice from the same recipe.

Suite `004-continue-headers` delivers the same message to two different mbox paths from two sibling recipes; `stats.duplicate_suppressed` must stay **zero** because each `(message_id, mbox, recipe_id)` triple is unique.

## Delivery deduplication (deliver.sh)

Every delivery goes through `deliver_record` in `/app/lib/procmail-sim/deliver.sh`. Before appending a row, check whether a row with the same triple already exists:

- `message_id`
- `mbox` (destination path)
- `recipe_id`

If the triple is already present, do not append another row. Increment `stats.duplicate_suppressed` once and return. If the triple is new, append the row and leave the counter unchanged.

`stats.duplicate_suppressed` counts blocked duplicate **append attempts** inside `deliver_record`, not the presence of `h` or `c` on a recipe. A correct pipeline should not generate duplicate triple attempts from normal `h`+`c` sibling delivery; the guard exists for overlapping paths or implementation mistakes, not as permission for `pipeline.sh` to call `deliver_record` twice for one recipe match.

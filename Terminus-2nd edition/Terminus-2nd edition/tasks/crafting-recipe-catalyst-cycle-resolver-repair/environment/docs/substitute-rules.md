# Substitute ingredient rules

For each input line in a recipe:

1. Let `base = input.item`.
2. Let `effective = substitutes[base]` if present, else `base`.
3. Let `required_qty = input.qty * batch_qty`.
4. Aggregate requirements by `effective` item id.

Inventory presence checks and deductions always use `effective` ids.

Applying the substitute map **after** scaling by `batch_qty` on the base item id is incorrect when the inventory only stores substitute items.

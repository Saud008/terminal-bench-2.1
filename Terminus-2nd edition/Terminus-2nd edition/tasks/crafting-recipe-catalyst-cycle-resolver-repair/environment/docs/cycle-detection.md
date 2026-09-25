# Recipe dependency cycles

Treat each recipe as a graph node. Add a directed edge `consumer -> producer` when:

- An **input** item is the `output.item` of another recipe, or
- A **catalyst** item is the `output.item` of another recipe.

Self-edges are ignored. Run DFS cycle detection. Populate `RecipeGraphReport`:

```json
{
  "recipe_count": 3,
  "edge_count": 2,
  "cyclic": true,
  "cycles": [["craft_ink", "craft_seal", "craft_ink"]]
}
```

Input-only edges are insufficient for catalyst chains.

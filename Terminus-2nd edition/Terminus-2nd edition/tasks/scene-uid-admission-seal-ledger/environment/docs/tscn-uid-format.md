# Packed-scene UID format (subset)

This control plane admits Godot 4 text scene packs only.

## Root scene line

```
[gd_scene load_steps=N format=3 uid="uid://xxxx"]
```

## External resources

```
[ext_resource type="PackedScene" uid="uid://yyyy" path="res://child.tscn" id="1_child"]
```

## Instancing

```
[node name="Child" parent="." instance=ExtResource("1_child")]
```

UID tokens always use the `uid="uid://…"` form. Matching is literal on the UID string.

## Sub-resources (when present)

```
[sub_resource type="RectangleShape2D" id="Rect_1" uid="uid://zzzz"]
```

Remap applies to these `uid="…"` attributes the same way as `ext_resource`.

## Seed overlay remap suffix

When seeds.json defines `remap_slot`, `remap_prefix`, and `remap_suffix_mod`, the overlay target UID is:

remap[remap_slot] = {remap_prefix}_{seed % remap_suffix_mod}

The divisor comes from the `remap_suffix_mod` field in /app/fixtures/seeds.json (currently 5). Example: prefix uid://player_new, seed 7, divisor 5 yields uid://player_new_2.

## UID graph edges

Only `ext_resource` lines with `type="PackedScene"` create directed UID graph edges. Other external resource types may include uid attributes for remapping but must not participate in cycle detection.

# Dynamic blocks

Each fragment may declare zero or more dynamic block templates. Templates list a name, comma-separated values, and template fields that may reference ${value}.

Expansion runs after all merge_override attributes are applied to the merged attribute map. Expanded rows must inherit overridden tag fields so dynamic ingress rows reflect the final tags.env value.

Dynamic expansion must not run on pre-override attribute state.

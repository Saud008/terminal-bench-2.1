# Opaque directory

A tar member whose final path component is `.wh..wh..opq` inside directory `D` marks `D` as opaque at that member layer index.

Opaque directories hide every lower-layer child path strictly under `D`. Children added at the same layer index or higher remain visible.

The opaque marker itself is not exported. Staging must record it with type `opaque` and path equal to `D`.

When an opaque marker is processed, remove surviving view entries whose path is a strict child of `D` and whose winning layer index is lower than the opaque marker layer index.

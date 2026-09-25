# Whiteout semantics

OCI and Docker layer tar archives encode deletions with whiteout marker files.

A tar member whose final path component is `.wh.<basename>` inside directory `D` is a whiteout marker. It does not appear in the exported manifest. It removes the path `D/<basename>` from the merged filesystem view contributed by lower layer indices.

Whiteout markers themselves must be recorded in staging with type `whiteout` and a `target` field holding the deleted absolute path.

Bundled layer1 includes a whiteout marker that removes /var/log/app.log from the merged view.

Bundled layer2 marks /opt/cache opaque and hides lower-layer children under that directory.

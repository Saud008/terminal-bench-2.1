# Modulemd default stream

modules.yaml in repodata uses document modulemd-defaults version 1. Default module streams are listed under data.module_defaults as an array of objects.

For each object, export module name from module_name, default stream from stream_name, and default profile from default_profile. Preserve module_defaults array order in staging but sort module rows by module name in the final attestation export.

Do not infer defaults by sorting stream names alphabetically or by picking the first YAML key.

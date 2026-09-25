# crush-bucket-catalog.md

Root buckets named default contain rack and host children. Host buckets list osd ids with sibling weights. Traversal for chooseleaf must recurse through rack buckets until host type buckets are collected.

# Resolver layout contract

Resolver seed content is copied from /app/fixtures/shared/resolv.conf.seed into the target rootfs tree.

When meta.json merged_usr is false, the destination is {tree}/etc/resolv.conf.

When meta.json merged_usr is true, the destination is {tree}/usr/etc/resolv.conf and must not write {tree}/etc/resolv.conf.

The staging manifest records resolv_target as the absolute path under /app used for the copy.

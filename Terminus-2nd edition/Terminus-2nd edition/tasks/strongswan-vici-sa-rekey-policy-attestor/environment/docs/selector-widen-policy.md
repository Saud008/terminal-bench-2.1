Selector widen policy

On child_rekey_done the merged local_ts and remote_ts must be the set union of the prior active CHILD_SA selectors and the new selectors from the event. After merge, every CIDR from the prior child must still be covered by at least one entry in the merged list (exact match or wider prefix per covers rule in replay). Intersection-only merge is invalid. Violations set selectors_ok false, reject_reason selector_narrowed.

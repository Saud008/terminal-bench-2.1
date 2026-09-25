# Airway expansion lemma

Before route matching, expand each flight `route_fixes` list: any token equal to an `airway_id` in `airways.json` is replaced by that airway's `fixes` sequence.

Expanding `AWY-7` (fixes `DEP MID ARR`) inside route `DEP AWY-7 ARR` yields the chain `DEP MID ARR` without duplicating an endpoint at a join: if the previous fix already equals the first fix of the inserted sequence, that first fix is not repeated.

A `route` kind NOTAM row closes a flight when its `route_fix` equals any expanded fix token, or when its `airway_id` equals a token before expansion. A match contributes a `route_restriction` closure whose `detail` is the matched route target.

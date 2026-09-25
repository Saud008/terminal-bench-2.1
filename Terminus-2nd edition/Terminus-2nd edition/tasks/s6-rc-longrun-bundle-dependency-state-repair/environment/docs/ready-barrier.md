Longrun readiness is evaluated against mock rc state in the state directory services.json map.

For each longrun service L, collect hard parents P where dep L hard P exists. L is ready only when every such parent has state up in services.json.

ready command output JSON contains bundle and longruns map. Each longrun entry has ready boolean and blocked_by list naming hard parents still down.

A longrun must not be marked ready when any hard parent is down, even if the longrun name appears early in an alphabetical service list.

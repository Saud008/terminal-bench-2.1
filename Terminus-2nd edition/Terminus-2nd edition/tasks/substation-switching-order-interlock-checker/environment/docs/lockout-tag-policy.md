# Lockout and tagout authenticity policy

Each loto.ticket JSON object is a lockout-authorization ticket containing:

- ticket_id: loto- prefix plus hex digest of seed:scenario:load_seq
- seed, scenario, load_seq
- active: true when compile-yard authenticity admission succeeds

Active lockout tags deny ALL operations (open and close) on listed equipment_ids. Equipment ids may name breakers or buses. A step touching locked equipment fails authenticity with reason lockout_active.

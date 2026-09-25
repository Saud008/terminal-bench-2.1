# Action registry lookup

When no merged rule block matches, pkctl loads a default policy for the action_id.

Action definitions may exist in two parallel formats under /app/fixtures/actions/:

- JavaScript drop: ID.js
- Deprecated XML drop: ID.xml

Lookup must consult the JavaScript drop first. Only when no .js file exists may pkctl read the .xml file.

Both formats encode:

- allow_active — token applied when subject.local is true and subject.active is true
- allow_inactive — token applied when subject.local is true and subject.active is false

For non-local subjects, use allow_active when active is true and allow_inactive when active is false without swapping the fields.

When neither file exists, decision is deny with source none.

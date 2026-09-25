# Boundary event ordering

Boundary events attach to a BPMN element id. A boundary may fire only after every job on that element has left the activating window.

The activating window for a job spans intent_at_ms inclusive through activating_until_ms exclusive. A boundary fire_at_ms must be greater than or equal to activating_until_ms for the attached element.

Interrupting boundaries appear in boundary_events with interrupting true. Non-interrupting boundaries still respect the same ordering gate.

# Engineering problem contract

Primary artifact: callout-roster.json with technician callout assignments and breach_horizon_summary under /app/output.

Workflow: load roster bundles, score SLA urgency, assign technicians under access policy, publish manifest with stable tie-break precedence.

Reasoning: policy precedence across SLA tiers, inclusive access-window constraint satisfaction, trapped-passenger severity weighting, and locked assignment persistence across repeat bind passes.

Verifier uses independent callout_refmath reference with randomized technician ids and building labels from generated bundles.

# Platform rubric — fiber-splice-loss-acceptance-atlas

**Task folder:** tasks/fiber-splice-loss-acceptance-atlas/

Agent applies TB3 loss threshold override when scanning reflections, +3
Agent applies TB3 reflection tolerance override during duplicate folding, +3
Agent detects loss events from adjacent sample power delta not absolute level, +3
Agent suppresses duplicate reflections within tolerance using epoch precedence, +3
Agent binds measured loss to route segments under spatial containment, +3
Agent attributes connector pair loss from inventory at segment junction, +2
Agent sums splice planned loss per segment from splice plan distances, +2
Agent accepts segments only when total loss stays within planned plus connector budget, +3
Agent publishes audit_digest over sorted segment ids with alphabetically sorted JSON keys, +2
Agent rebuilds fsplatlas from /app sources with cargo release locked, +2
Agent honors TB3_TRACE_ROOT for hidden trace fixtures, +2
Agent increments capture cache load_generation across repeated load-capture, +2
Agent leaves backscatter decoy module off the publish hot path, +1
Agent uses wrong power field when computing adjacent sample delta, -3
Agent skips duplicate suppression or keeps lower epoch reflection, -3
Agent binds events to wrong segment outside containment window, -3
Agent omits connector pair loss from total budget ledger, -2
Agent accepts segments when measured loss exceeds planned budget, -3

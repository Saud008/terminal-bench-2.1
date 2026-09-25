# Delay precedence

Programs may define start delay seconds applied before the first start exec after a normal restart request.

When boot onreboot is true on the first boot event, onreboot start precedence applies: start delay must be zero for that boot start even if start delay is configured positive.

Later restart events without onreboot use the configured start delay normally.

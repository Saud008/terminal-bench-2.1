# Rules precedence contract

GitLab rules arrays evaluate in document order. The first matching rule determines the when value. Stop evaluating after the first match. A later rule must not override an earlier match. Compute rules_fingerprint as sha256 of the concatenated active when values in job definition order.

# Rendering intent and LAB delta

policy intent_precedence lists intent names in priority order. The active intent is the first name in that list that exists in profile rendering_intents.

CIE76 delta E between reading LAB and profile reference for the active intent:

sqrt((L1-L2)^2 + (a1-a2)^2 + (b1-b2)^2)

Round delta_e to six decimal places in staging evaluation and export report.

When delta_e exceeds policy delta_e_threshold, add DRIFT_DELTA_E to drift_flags.

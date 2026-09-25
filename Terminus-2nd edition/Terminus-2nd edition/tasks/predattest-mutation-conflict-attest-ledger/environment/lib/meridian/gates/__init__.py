"""Swappable hold-preview gate modules.

Each module owns exactly one rollout decision the compile pipeline calls
into. The verifier overlays broken/fixed variants of these files one at a
time, so every gate module stays self-contained with a single decision
entry point.
"""

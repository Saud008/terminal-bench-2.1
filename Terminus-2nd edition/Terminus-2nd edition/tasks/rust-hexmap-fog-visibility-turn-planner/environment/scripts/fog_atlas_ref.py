#!/usr/bin/env python3
"""Optional fog atlas field helper for local playtest checks."""

def win_condition_met(visible_count: int, target_reveal: int) -> bool:
    return visible_count >= target_reveal

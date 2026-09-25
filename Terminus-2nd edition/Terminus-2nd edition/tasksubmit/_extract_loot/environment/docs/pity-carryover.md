# Pity counter and seasonal carryover

Each player maintains pity_legendary in the pity ledger. On a pull event:

- If rarity is legendary: reset pity_legendary to 0 after processing the grant or duplicate conversion.
- If rarity is not legendary: increment pity_legendary by 1 after processing.

When a player event season_id differs from the season_id stored for that player in the ledger, apply carryover before processing the pull:

```
pity_legendary = floor(old_pity_legendary * new_season.carry_ratio)
```

Use the NEW season carry_ratio from the season config for the event season_id, not the previous season ratio. Carry applies once per season transition per player.

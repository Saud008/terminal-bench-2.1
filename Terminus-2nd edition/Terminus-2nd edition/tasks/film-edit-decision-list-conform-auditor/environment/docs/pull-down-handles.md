# Pull-down handles

When pulldown is 23976, handle frame budgets scale source spans from 24000/1001 to nominal 30 fps frame counts using integer math: budget = (raw_span * 24000 + 11988) / 23976.

Raw span uses non-drop frame math on source in and source out even when the bundle uses drop-frame record timecodes.

Handle overflow findings fire when source out frames exceed available frames in the source manifest for the resolved reel.

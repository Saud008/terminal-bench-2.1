# Platform rubric — charity-grant-restriction-spend-tracker

**Task folder:** tasks/charity-grant-restriction-spend-tracker/
**Written:** 2026-07-20T02:10:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent loads grant portfolio rows into SQLite via grantctl load-portfolio, +2
Agent applies most specific restriction when multiple fund rules overlap a grant, +3
Agent honors amendment effective dates when computing temporal spend ceilings, +3
Agent rejects expenses outside the category allow-list for each restriction, +3
Agent resolves legacy project code aliases before mapping expenses to grants, +3
Agent increments amendment_pass in amendment-pass.json only after apply-amendments, +2
Agent blocks publish-spend-atlas when amendment_pass is zero, +2
Agent rolls remaining restricted balance per grant in spend-atlas.json, +3
Agent prevents duplicate spend totals on repeated publish-spend-atlas runs, +3
Agent emits rejections as a JSON array, using [] when no expenses are rejected, +2
Agent produces a working /app/bin/grantctl that satisfies load-portfolio, apply-amendments, and publish-spend-atlas contracts after source edits, +2
Agent correctly reconciles portfolios that combine overlap specificity with legacy aliases and temporal amendment windows with category allow-lists, +2
Agent runs apply-amendments and publish-spend-atlas without --scenario against the loaded portfolio database, +2
Agent picks least specific restriction when overlap rules conflict, -3
Agent applies latest amendment retroactively ignoring effective dates, -3
Agent accepts all expense categories without allow-list enforcement, -3
Agent double-counts spend rows on atlas publish rerun, -3
Agent emits null for rejections when the rejection list is empty, -2
Agent requires --scenario on apply-amendments or publish-spend-atlas, -3

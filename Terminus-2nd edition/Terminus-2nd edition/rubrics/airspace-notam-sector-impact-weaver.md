# Platform rubric — airspace-notam-sector-impact-weaver

**Task folder:** tasks/airspace-notam-sector-impact-weaver/

Agent implements amendment suppression keeping highest series amendment, +3
Agent evaluates crossing-midnight activation windows correctly, +3
Agent uses ray-cast point-in-polygon for concave sector NOTAMs, +3
Agent normalizes runway designators before closure matching, +2
Agent expands airway catalog tokens before route restriction matching, +3
Agent includes policy in bundle digest computation, +2
Agent increments weave_revision on each weave-impact pass, +2
Agent sorts route impacts by flight_id then notam_id ascending in export, +2
Agent blocks emit-report when weave_revision is zero, +2
Agent matches full impact report to independent reference math, +3
Agent treats NOTAM bodies as plain text grep without geometry, -3
Agent keeps superseded lower amendments in active_notams, -3
Agent uses bounding-box only checks for concave sector polygons, -3
Agent skips airway expansion and matches only raw route tokens, -3
Agent emits report with reversed impact sort order, -2

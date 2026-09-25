# Engineering problem contract

nomrep implements a Nomad placement affinity atlas workflow: scenario load to placement buffer, compile atlas journal with mountlink joins and spread-adjusted ranking, publish atlas with persistence.

Independent reference math in pytest validates mountlink rows, drain eligibility, stale suppression, reschedule totals, spread penalties, placement ranking, and audit digest without reading Go sources.

The decoy spread hint scorer is not on the load, compile, or publish hot path.

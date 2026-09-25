# CANCEL versus BYE

For dialogs not yet answered (no 2xx to INVITE), CANCEL ends the dialog with disposition canceled and suppresses later BYE.

After answer, BYE ends dialog with disposition completed. If both arrive, precedence follows answer state at event time.

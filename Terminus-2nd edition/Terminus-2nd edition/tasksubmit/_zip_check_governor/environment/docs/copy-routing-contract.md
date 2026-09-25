# Copy routing contract

Select the first available copy for the item using this order:

1. available copy at pickup_branch_id with smallest copy_id
2. if none, available copy at another branch that allows_interbranch_transfer with smallest copy_id

Never assign copies whose status is not exactly available.

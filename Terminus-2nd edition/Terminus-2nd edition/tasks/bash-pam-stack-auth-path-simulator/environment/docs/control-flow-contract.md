# Auth stack control flow

Simulation covers auth-type modules only, in file order after include expansion.

Every auth module in the expanded sequence is appended to `steps` in execution index order, including modules that appear after a short-circuit. Short-circuit only stops further control-flag evaluation of the final verdict; it does not truncate the steps array.

requisite: on non-success result, set the final verdict to that result with reason `requisite_failure` and short-circuit control-flag evaluation immediately. Continue iterating the remaining auth modules only to append their step records (do not apply later required / requisite / sufficient / optional rules to the verdict).

required: on non-success, record failure and continue. If any required module failed and the stack was not short-circuited by sufficient success or requisite failure, return the first required failure with reason `required_failure`.

sufficient: on success when no prior required module failed, set success with reason `sufficient_success` and short-circuit control-flag evaluation the same way as requisite (remaining modules are still appended to `steps`; later flags do not change the verdict).

optional: never changes final verdict alone.

If no rule short-circuits the stack, return success with reason `ok`.

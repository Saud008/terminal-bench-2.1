# Spare hold gate contract

The fleet-wide `spare_holds` list names devices that are reserved for another array or maintenance activity and must not be consumed as a reshape spare.

If any device listed in an array's `spares` array appears anywhere in the fleet's `spare_holds` list, that array is blocked with reason `blocked_spare_hold`.

This check must inspect every entry in the array's `spares` array, not only the first entry. An array with two spares where only the second spare is held must still be blocked.

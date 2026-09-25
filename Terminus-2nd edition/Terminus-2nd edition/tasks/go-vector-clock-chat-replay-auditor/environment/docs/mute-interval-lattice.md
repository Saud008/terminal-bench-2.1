# Mute interval lattice

Mute windows are half-open intervals on the chat timeline, separate from moderation rank outcomes.

## Visibility per user

| Mode | Meaning |
|------|---------|
| active | User may send visible messages |
| silenced | User inside [start_ms, end_ms) mute interval |

## Interval rules

mute_start at timestamp T moves the user into silenced when T is greater than or equal to start_ms and strictly less than end_ms.

mute_end at timestamp T returns the user to active only when T is greater than or equal to end_ms. End is exclusive for leak detection.

## Interaction with moderation

Ban or kick moderation hides messages regardless of mute interval. Mute leak findings apply only when moderation rank does not already hide the sender.

## Reconcile ordering

The reconcile pass evaluates mute intervals after moderation precedence so concurrent moderation and mute events resolve in rank order first.

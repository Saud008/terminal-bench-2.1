# Death and pin

On death (`hp <= 0` after bleed or otherwise):

- Set `alive` to false, `hp` to 0.
- Clear `pinned` and `stunned`.

Dead actors must not remain pinned in `actors_final` or persistence state.

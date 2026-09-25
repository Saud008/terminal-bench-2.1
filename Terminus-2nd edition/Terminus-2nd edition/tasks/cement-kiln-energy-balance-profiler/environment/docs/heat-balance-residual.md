# Heat balance residual

energy_in_mj sums staged fuel batch energy_mj values. clinker_out_t sums clinker window tonnes. clinker_energy_mj sums clinker_t * default_specific_heat_mj_per_t.

residual_mj = energy_in_mj - clinker_energy_mj - heat_loss_mj. residual_mj_per_t = residual_mj / clinker_out_t when clinker_out_t > 0.

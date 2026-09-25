use crate::types::{BalanceScratch, ClinkerWindow, Config, FuelBatch};

pub fn score_balance(
    cfg: &Config,
    run_id: &str,
    fuels: &[FuelBatch],
    clinker: &[ClinkerWindow],
    heat_loss_mj: f64,
) -> BalanceScratch {
    let energy_in_mj: f64 = fuels.iter().map(|f| f.energy_mj).sum();
    let clinker_out_t: f64 = clinker.iter().map(|c| c.clinker_t).sum();
    let clinker_energy_mj: f64 = clinker
        .iter()
        .map(|c| c.clinker_t * cfg.default_specific_heat_mj_per_t)
        .sum();
    let residual_mj = energy_in_mj - clinker_energy_mj - heat_loss_mj;
    let residual_mj_per_t = if clinker_out_t > 0.0 {
        residual_mj / clinker_out_t
    } else {
        0.0
    };
    BalanceScratch {
        run_id: run_id.to_string(),
        energy_in_mj,
        clinker_out_t,
        clinker_energy_mj,
        heat_loss_mj,
        residual_mj,
        residual_mj_per_t,
    }
}

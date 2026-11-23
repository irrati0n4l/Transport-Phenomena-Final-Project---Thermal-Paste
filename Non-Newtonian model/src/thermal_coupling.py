r"""
thermal_coupling.py -- Component 3: Energy transport & chip-failure model.

Takes the bondline history (h(t), R(t)) from the momentum engine and applies
steady 1D Fourier conduction across the gap (lateral spreading in the
lid/heatsink is neglected -- conservative for the TIM layer itself).

Parallel thermal-resistance network over the (equivalent-disk) die area:

    covered path:    R_cov = h / (k_TIM * A_cov),           A_cov = pi R^2
    air-gap path:    R_air = h / (k_air * (A_die - A_cov))   (only if R < R_die)

    1/R_TIM,eff = 1/R_cov + 1/R_air = (k_TIM A_cov + k_air A_unc) / h
    Delta T_TIM = Q * R_TIM,eff

Because the heat load Q is fixed by the GPU, under-coverage also produces a
*local* hotspot over the uncovered perimeter, bounded by 1D conduction of the
die-average flux through air:  Delta T_hot = q'' h / k_air.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from params import GPU_700W, THERMAL, GPUSpec, ThermalSpec

__all__ = [
    "covered_area", "coverage_fraction", "tim_resistance",
    "delta_T_tim", "delta_T_hotspot", "ThermalState", "thermal_state",
    "full_coverage_resistance",
]


def covered_area(R, gpu: GPUSpec = GPU_700W):
    """Wetted die area A_cov = pi min(R, R_die)^2  [m^2]."""
    return np.pi * np.minimum(np.asarray(R, float), gpu.R_die) ** 2


def coverage_fraction(R, gpu: GPUSpec = GPU_700W):
    """A_cov / A_die  [-]."""
    return covered_area(R, gpu) / gpu.A_die


def tim_resistance(h, R, gpu: GPUSpec = GPU_700W, th: ThermalSpec = THERMAL):
    """Effective bondline resistance of the parallel TIM/air network  [K/W]."""
    h = np.asarray(h, float)
    A_cov = covered_area(R, gpu)
    A_unc = np.maximum(gpu.A_die - A_cov, 0.0)
    return h / (th.k_tim * A_cov + th.k_air * A_unc)


def full_coverage_resistance(h, gpu: GPUSpec = GPU_700W, th: ThermalSpec = THERMAL):
    """Ideal fully wetted bondline resistance h/(k_TIM A_die)  [K/W]."""
    return np.asarray(h, float) / (th.k_tim * gpu.A_die)


def delta_T_tim(h, R, gpu: GPUSpec = GPU_700W, th: ThermalSpec = THERMAL):
    """Die-average temperature rise across the TIM, Q * R_TIM,eff  [K]."""
    return gpu.Q * tim_resistance(h, R, gpu, th)


def delta_T_hotspot(h, R, gpu: GPUSpec = GPU_700W, th: ThermalSpec = THERMAL):
    """Local rise over an *uncovered* region, q'' h / k_air (0 if fully covered) [K]."""
    h = np.asarray(h, float)
    uncovered = np.asarray(R, float) < gpu.R_die * (1.0 - 1e-12)
    return np.where(uncovered, gpu.q_flux * h / th.k_air, 0.0)


@dataclass
class ThermalState:
    """Thermal readouts for a bondline history."""
    coverage: np.ndarray        # [-]
    R_tim: np.ndarray           # [K/W]
    dT_tim: np.ndarray          # [K]
    dT_hotspot: np.ndarray      # [K]
    penalty: np.ndarray         # R_tim / R_full-coverage at the same h  [-]


def thermal_state(h, R, gpu: GPUSpec = GPU_700W, th: ThermalSpec = THERMAL) -> ThermalState:
    """Bundle all thermal outputs for arrays h(t), R(t)."""
    Rt = tim_resistance(h, R, gpu, th)
    return ThermalState(
        coverage=coverage_fraction(R, gpu),
        R_tim=Rt,
        dT_tim=gpu.Q * Rt,
        dT_hotspot=delta_T_hotspot(h, R, gpu, th),
        penalty=Rt / full_coverage_resistance(h, gpu, th),
    )

"""
params.py -- Component 1: Hardware benchmark & material configuration.

Single source of truth for every number used by the physics, verification,
figure and notebook layers.  All quantities are in SI units.

Swap the GPU (e.g. H100 -> B200) or the paste by editing *this file only*;
every downstream module reads its inputs from the dataclasses defined here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Optional, Union

__all__ = [
    "GPUSpec", "DropletSpec", "ThermalSpec",
    "Newtonian", "PowerLaw", "Bingham", "Fluid",
    "GPU_700W", "DROPLET", "THERMAL",
    "NEWTONIAN", "SHEAR_THINNING", "SHEAR_THICKENING", "BINGHAM",
    "MOUNT_TIME", "replace",
]


# --------------------------------------------------------------------------- #
# Hardware benchmark
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class GPUSpec:
    """700 W AI GPU accelerator (H100-class) modelled as an equivalent disk."""
    name: str = "700 W AI GPU accelerator (H100-class)"
    A_die: float = 814e-6        # die area                      [m^2]
    Q: float = 700.0             # heat load through the TIM     [W]
    F0: float = 400.0            # constant clamping force       [N]

    @property
    def R_die(self) -> float:
        """Equivalent-disk die radius R_die = sqrt(A_die/pi)  [m] (~16.1 mm)."""
        return math.sqrt(self.A_die / math.pi)

    @property
    def side(self) -> float:
        """Side length of the (square) physical die [m] (~28.5 mm)."""
        return math.sqrt(self.A_die)

    @property
    def q_flux(self) -> float:
        """Average die heat flux q'' = Q/A_die  [W/m^2] (~86 W/cm^2)."""
        return self.Q / self.A_die


@dataclass(frozen=True)
class DropletSpec:
    """Constant-volume 'pea-dot' of paste dispensed at the die centre."""
    V0: float = 50e-9            # dispensed paste volume        [m^3] (50 mm^3)
    h0: float = 1.0e-3           # initial dot height            [m]

    @property
    def R0(self) -> float:
        """Initial dot radius from V0 = pi R0^2 h0  [m]."""
        return math.sqrt(self.V0 / (math.pi * self.h0))


@dataclass(frozen=True)
class ThermalSpec:
    """Thermal conductivities for the parallel TIM / air-gap network."""
    k_tim: float = 5.0           # paste conductivity            [W/(m K)]
    k_air: float = 0.026         # trapped-air conductivity      [W/(m K)]


# --------------------------------------------------------------------------- #
# Constitutive (rheology) models -- "closure is material-specific"
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Newtonian:
    """tau = mu * gamma_dot."""
    mu: float = 100.0            # dynamic viscosity             [Pa s]
    rho: float = 2500.0          # density (filled silicone)     [kg/m^3]
    label: str = "Newtonian"


@dataclass(frozen=True)
class PowerLaw:
    """tau = K |gamma_dot|^(n-1) gamma_dot  (n<1 thinning, n>1 thickening)."""
    K: float = 100.0             # consistency index             [Pa s^n]
    n: float = 0.5               # flow-behaviour index          [-]
    rho: float = 2500.0
    label: str = "Power-law"


@dataclass(frozen=True)
class Bingham:
    """|tau| > tau_y : tau = tau_y sgn(gamma_dot) + mu_p gamma_dot ; else rigid."""
    mu_p: float = 100.0          # plastic viscosity             [Pa s]
    tau_y: float = 250.0         # yield stress                  [Pa]
    rho: float = 2500.0
    label: str = "Bingham"


Fluid = Union[Newtonian, PowerLaw, Bingham]

# --------------------------------------------------------------------------- #
# Default benchmark instances
# --------------------------------------------------------------------------- #
GPU_700W = GPUSpec()
DROPLET = DropletSpec()
THERMAL = ThermalSpec()

NEWTONIAN = Newtonian()
SHEAR_THINNING = PowerLaw(n=0.5, label="Shear-thinning (n=0.5)")
SHEAR_THICKENING = PowerLaw(n=1.3, label="Shear-thickening (n=1.3)")
BINGHAM = Bingham(label=r"Bingham ($\tau_y$=250 Pa)")

MOUNT_TIME: float = 60.0         # representative heatsink-mount hold time [s]


def describe() -> str:
    """Human-readable summary of the benchmark (used by notebook/README)."""
    g, d, th = GPU_700W, DROPLET, THERMAL
    return (
        f"{g.name}\n"
        f"  A_die = {g.A_die*1e6:.0f} mm^2  ->  R_die = {g.R_die*1e3:.2f} mm\n"
        f"  Q = {g.Q:.0f} W  ->  q'' = {g.q_flux/1e4:.1f} W/cm^2\n"
        f"  F0 = {g.F0:.0f} N\n"
        f"  V0 = {d.V0*1e9:.0f} mm^3, h0 = {d.h0*1e3:.2f} mm -> R0 = {d.R0*1e3:.2f} mm\n"
        f"  k_TIM = {th.k_tim} W/mK, k_air = {th.k_air} W/mK"
    )


if __name__ == "__main__":
    print(describe())

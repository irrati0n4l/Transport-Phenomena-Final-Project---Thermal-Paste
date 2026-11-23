r"""
rheology_models.py -- Component 2: Momentum-transport engine.

"Conservation is universal; closure is material-specific."

Every function here follows from the same three steps:

1. **RTT / continuity on a deformable control volume.**  For a disk of radius
   ``r`` inside the gap, mass conservation gives the radial volume flux per
   unit circumference

   .. math::  q(r) = \int_0^h u_r\,dz = \frac{r\,(-\dot h)}{2}.

2. **Lubrication reduction** (``eps = h/R << 1``, ``Re_sq << 1``): the
   r-momentum equation collapses to ``0 = -dp/dr + d(tau_rz)/dz`` so with
   ``G = -dp/dr`` the shear stress is linear across the gap,
   ``tau_rz = -G * zeta`` (``zeta = z - h/2``, midplane symmetry).

3. **Constitutive closure** (Newtonian / power-law / Bingham) gives
   ``u_r(z)``, hence ``q(G)``.  Equating with step 1 gives ``G(r)``, then
   ``p(r)`` and the squeeze force ``F = \int_0^R p 2 pi r dr``.

Constant-force loading ``F = F0`` then yields an ODE for ``h(t)``.
Geometry: constant-volume pea-dot ``V0 = pi R^2 h`` until ``R`` reaches the
die edge ``R_die``; afterwards the wetted radius is pinned at ``R_die`` and the
excess paste is expelled (constant-area squeeze, ``p = p_inf`` at the die edge).
The transition is continuous in ``h``, ``dh/dt`` and ``F``.

Coordinates: lower plate ``z = 0``, upper plate ``z = h``.  All SI units.
Only numpy is required.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from params import Bingham, Fluid, Newtonian, PowerLaw

__all__ = [
    "wetted_radius", "cap_thickness",
    # Newtonian (Stefan)
    "newtonian_force", "newtonian_rate", "newtonian_h",
    # Power-law (Scott)
    "power_law_force", "power_law_rate", "power_law_h",
    # Bingham (Covey-Stanmore)
    "bingham_plug_fraction", "bingham_yield_fraction", "bingham_Phi", "bingham_force", "bingham_rate",
    "bingham_stall", "bingham_critical_yield_stress", "bingham_critical_force", "BinghamSolution",
    # generic
    "squeeze_force", "squeeze_rate", "SqueezeResult", "solve_squeeze",
    # local fields
    "pressure_gradient", "pressure", "velocity", "shear_stress",
    "plug_half_thickness",
]

_TINY = 1e-300


# =========================================================================== #
# Geometry: constant-volume pea-dot, capped at the die edge
# =========================================================================== #
def wetted_radius(h, V0: float, R_die: Optional[float] = None):
    r"""R(h) = min( sqrt(V0/(pi h)), R_die )."""
    R = np.sqrt(V0 / (np.pi * np.asarray(h, dtype=float)))
    return R if R_die is None else np.minimum(R, R_die)


def cap_thickness(V0: float, R_die: Optional[float]) -> float:
    r"""Thickness h_c = V0/(pi R_die^2) at which the dot reaches the die edge."""
    return 0.0 if R_die is None else V0 / (np.pi * R_die**2)


# =========================================================================== #
# Newtonian -- Stefan (1874)
# =========================================================================== #
def newtonian_force(h, R, W, mu: float):
    r"""F = 3 pi mu W R^4 / (2 h^3),  W = -dh/dt.

    With R^2 = V0/(pi h):  F = 3 mu V0^2 W / (2 pi h^5).
    """
    return 3.0 * np.pi * mu * W * R**4 / (2.0 * h**3)


def newtonian_rate(h, F0: float, mu: float, V0: float, R_die=None):
    r"""Squeeze rate W(h) = -dh/dt from inverting :func:`newtonian_force`."""
    h = np.asarray(h, dtype=float)
    R = wetted_radius(h, V0, R_die)
    return 2.0 * F0 * h**3 / (3.0 * np.pi * mu * R**4)


def newtonian_h(t, F0: float, mu: float, V0: float, h0: float, R_die=None):
    r"""Closed-form h(t) for constant force, constant volume, die-capped.

    Phase 1 (R < R_die):  h = h0 (1 + 8 pi F0 h0^4 t / (3 mu V0^2))^{-1/4}
    Phase 2 (R = R_die):  h^{-2} = h_c^{-2} + 4 F0 (t - t_c)/(3 pi mu R_die^4)
    """
    t = np.asarray(t, dtype=float)
    h1 = h0 * (1.0 + 8.0 * np.pi * F0 * h0**4 * t / (3.0 * mu * V0**2)) ** -0.25
    hc = cap_thickness(V0, R_die)
    if R_die is None:
        return h1
    if h0 <= hc:
        hc, tc = h0, 0.0
    else:
        tc = ((h0 / hc) ** 4 - 1.0) * 3.0 * mu * V0**2 / (8.0 * np.pi * F0 * h0**4)
    h2 = (hc**-2 + 4.0 * F0 * np.maximum(t - tc, 0.0) / (3.0 * np.pi * mu * R_die**4)) ** -0.5
    return np.where(t < tc, h1, h2)


# =========================================================================== #
# Power-law -- Scott (1931)
# =========================================================================== #
def _pl_coeff(n: float) -> float:
    """((2n+1)/n)^n -- recurring power-law flux constant."""
    return ((2.0 * n + 1.0) / n) ** n


def power_law_force(h, R, W, K: float, n: float):
    r"""F = 2 pi K/(n+3) ((2n+1)/n)^n W^n R^{n+3} / h^{2n+1}.

    With R^2 = V0/(pi h) this is Scott's constant-volume law
    F = 2piK/(n+3) ((2n+1)/n)^n (V0/pi)^{(n+3)/2} W^n / h^{(5n+5)/2}.
    """
    return 2.0 * np.pi * K / (n + 3.0) * _pl_coeff(n) * W**n * R ** (n + 3.0) / h ** (2.0 * n + 1.0)


def power_law_rate(h, F0: float, K: float, n: float, V0: float, R_die=None):
    """Squeeze rate W(h) from inverting :func:`power_law_force`."""
    h = np.asarray(h, dtype=float)
    R = wetted_radius(h, V0, R_die)
    return (F0 * (n + 3.0) * h ** (2.0 * n + 1.0)
            / (2.0 * np.pi * K * _pl_coeff(n) * R ** (n + 3.0))) ** (1.0 / n)


def power_law_h(t, fluid: PowerLaw, F0: float, V0: float, h0: float, R_die=None):
    r"""Closed-form h(t) for a power-law fluid (constant force, die-capped).

    Phase 1, constant volume:  -dh/dt = A h^m,  m = (5n+5)/(2n)
        h(t) = [h0^{1-m} + (m-1) A t]^{1/(1-m)}   =>  h ~ t^{-2n/(3n+5)}
    Phase 2, constant area:    -dh/dt = B h^k,  k = (2n+1)/n
        h(t) = [h_c^{1-k} + (k-1) B (t-t_c)]^{1/(1-k)}
    """
    K, n = fluid.K, fluid.n
    t = np.asarray(t, dtype=float)
    c = _pl_coeff(n)
    m = (5.0 * n + 5.0) / (2.0 * n)
    A = (F0 * (n + 3.0) / (2.0 * np.pi * K * c)) ** (1.0 / n) * (np.pi / V0) ** ((n + 3.0) / (2.0 * n))
    hc = cap_thickness(V0, R_die)

    if h0 <= hc:                      # dot already wider than die: pure phase 2
        hc_eff, tc = h0, 0.0
    else:
        hc_eff = hc
        tc = (hc ** (1.0 - m) - h0 ** (1.0 - m)) / ((m - 1.0) * A) if hc > 0 else np.inf

    h1 = (h0 ** (1.0 - m) + (m - 1.0) * A * t) ** (1.0 / (1.0 - m))
    if R_die is None or not np.isfinite(tc):
        return h1

    k = (2.0 * n + 1.0) / n
    B = (F0 * (n + 3.0) / (2.0 * np.pi * K * c * R_die ** (n + 3.0))) ** (1.0 / n)
    h2 = (hc_eff ** (1.0 - k) + (k - 1.0) * B * np.maximum(t - tc, 0.0)) ** (1.0 / (1.0 - k))
    return np.where(t < tc, h1, h2)


# =========================================================================== #
# Bingham -- Covey & Stanmore (1981) lubrication solution
# =========================================================================== #
# Slot flow of a Bingham fluid (Buckingham-Reiner) gives, with the plug
# fraction xi0 = 2 tau_y / (h G) = (plug thickness)/h in (0, 1):
#
#     q = h^3 G / (12 mu_p) * (1 - 3/2 xi0 + 1/2 xi0^3)
#
# Setting q = r W / 2 and eliminating G = 2 tau_y/(h xi0):
#
#     S(r) := 3 mu_p r W / (tau_y h^2) = (1 - xi0)^2 (2 + xi0) / (2 xi0)
#
# i.e. the normalised cubic  xi^3 - (3 + 2S) xi + 2 = 0,  root in (0, 1].
# S -> 0 at the centre (xi -> 1, G -> 2 tau_y/h: no singularity) and
# S -> inf in the Newtonian limit (xi -> 1/S).
# The global parameter is Lambda = S(R) = 3/Bn with Bn = tau_y h^2/(mu_p R W).
# --------------------------------------------------------------------------- #
def bingham_plug_fraction(S):
    r"""Exact root xi0(S) in (0, 1] of  xi^3 - (3+2S) xi + 2 = 0.

    Trigonometric (Viete) solution written in a cancellation-free form:
    with a = 3/(3+2S),  xi0 = (2/sqrt(a)) sin( arcsin(a^{3/2}) / 3 ).
    Monotone decreasing from 1 (S=0) to ~1/S (S -> inf).  Fully vectorised;
    never diverges, so no bracketing root-finder is needed near r = 0.
    """
    S = np.maximum(np.asarray(S, dtype=float), 0.0)
    a = 3.0 / (3.0 + 2.0 * S)
    one_minus_y = -np.expm1(1.5 * np.log1p(-2.0 * S / (3.0 + 2.0 * S)))
    y = a**1.5
    # near y = 1 use arcsin(y) = pi/2 - 2 arcsin(sqrt((1-y)/2)) (no cancellation);
    # elsewhere the direct arcsin is accurate.
    asin_y = np.where(
        y > 0.5,
        0.5 * np.pi - 2.0 * np.arcsin(np.sqrt(np.clip(0.5 * one_minus_y, 0.0, 1.0))),
        np.arcsin(np.minimum(y, 1.0)),
    )
    return 2.0 / np.sqrt(a) * np.sin(asin_y / 3.0)


def bingham_yield_fraction(S):
    r"""delta(S) = 1 - xi0(S): yielded fraction of the gap, computed without
    cancellation.  For small S it solves  delta^2 (3 - delta) = 2 S (1 - delta)
    by Newton iteration from delta ~ sqrt(2S/3)."""
    S = np.maximum(np.asarray(S, dtype=float), 0.0)
    d = 1.0 - bingham_plug_fraction(S)
    small = S < 0.05
    if np.any(small):
        s = S[small] if d.ndim else S
        x = np.sqrt(2.0 * s / 3.0)
        for _ in range(8):
            g = x * x * (3.0 - x) - 2.0 * s * (1.0 - x)
            dg = 6.0 * x - 3.0 * x * x + 2.0 * s
            x = x - np.where(dg > 0, g / np.where(dg > 0, dg, 1.0), 0.0)
        if d.ndim:
            d[small] = x
        else:
            d = x
    return d


def _S_of_delta(d):
    """S as a function of delta = 1 - xi0."""
    return d * d * (3.0 - d) / (2.0 * (1.0 - d))


# Gauss-Legendre nodes on [0, 1]
_GL_X, _GL_W = np.polynomial.legendre.leggauss(64)
_GL_X = 0.5 * (_GL_X + 1.0)
_GL_W = 0.5 * _GL_W


def _I_antideriv(xi):
    """Antiderivative of S(xi)^2 (xi^-3 - 1) d xi."""
    return (-0.25 * xi**-4 + xi**-3 - 1.125 * xi**-2 + 1.5 * np.log(xi)
            - 2.25 * xi - 0.375 * xi**2 + 0.5 * xi**3 - 0.05 * xi**5)


def bingham_Phi(Lam):
    r"""Dimensionless squeeze-force function

    .. math:: \Phi(\Lambda) = 3\int_0^1 \frac{s^2}{\xi_0(\Lambda s)}\,ds,
              \qquad F = \frac{2\pi\tau_y R^3}{3h}\,\Phi(\Lambda).

    Phi(0) = 1 (plastic limit),  Phi ~ 3 Lambda/4 + 3/2 (Newtonian limit).
    Evaluated by changing variable s -> xi (exact antiderivative for
    Lambda >= 1, 64-pt Gauss-Legendre in delta = 1 - xi otherwise).
    """
    Lam = np.atleast_1d(np.asarray(Lam, dtype=float))
    out = np.ones_like(Lam)

    big = Lam >= 1.0
    if np.any(big):
        xiL = bingham_plug_fraction(Lam[big])
        out[big] = 3.0 * (_I_antideriv(1.0) - _I_antideriv(xiL)) / Lam[big] ** 3

    small = (~big) & (Lam > 0.0)
    if np.any(small):
        dL = bingham_yield_fraction(Lam[small])[:, None]
        d = dL * _GL_X[None, :]                       # delta in (0, delta_Lambda)
        # integrand S^2 (xi^-3 - 1) d xi,  xi^-3 - 1 = d (3 - 3d + d^2)/(1-d)^3
        f = _S_of_delta(d) ** 2 * d * (3.0 - 3.0 * d + d * d) / (1.0 - d) ** 3
        integral = dL[:, 0] * (f @ _GL_W)
        out[small] = 3.0 * integral / Lam[small] ** 3
    return out


def bingham_force(h, R, W, mu_p: float, tau_y: float):
    """F(h, R, W) for a Bingham fluid (exact lubrication result)."""
    if tau_y <= 0.0:
        return newtonian_force(h, R, W, mu_p)
    Lam = 3.0 * mu_p * R * W / (tau_y * h**2)
    return 2.0 * np.pi * tau_y * R**3 / (3.0 * h) * bingham_Phi(Lam).reshape(np.shape(Lam))


def _invert_Phi(target):
    """Vectorised solve of Phi(Lambda) = target (target > 1) by log-bisection.

    Uses the rigorous bracket 3L/4 + 1 <= Phi(L) <= 3L/4 + 3/2.
    """
    target = np.atleast_1d(np.asarray(target, dtype=float))
    hi = np.maximum(4.0 * (target - 1.0) / 3.0, 1e-300)
    lo_log = np.log(hi) - 120.0
    hi_log = np.log(hi)
    for _ in range(200):
        mid = 0.5 * (lo_log + hi_log)
        too_big = bingham_Phi(np.exp(mid)) > target
        hi_log = np.where(too_big, mid, hi_log)
        lo_log = np.where(too_big, lo_log, mid)
    return np.exp(0.5 * (lo_log + hi_log))


def bingham_stall(F0: float, tau_y: float, V0: float, R_die=None):
    r"""Plastic-limit stall thickness h* and final spread radius R*.

    Plastic limit (Phi = 1):  F0 = 2 pi tau_y R^3 / (3 h).
    Constant volume:  h* = (2 tau_y V0^{3/2} / (3 sqrt(pi) F0))^{2/5},
                      R* = sqrt(V0/(pi h*)).
    If R* >= R_die the die is fully covered before stalling and the stall
    occurs in the constant-area phase: h* = 2 pi tau_y R_die^3 / (3 F0).

    Returns (h_star, R_star, covered) where ``covered`` is True when R* >= R_die.
    """
    if tau_y <= 0.0:
        return 0.0, (R_die if R_die is not None else np.inf), True
    h_vol = (2.0 * tau_y * V0**1.5 / (3.0 * np.sqrt(np.pi) * F0)) ** 0.4
    R_vol = np.sqrt(V0 / (np.pi * h_vol))
    if R_die is None or R_vol < R_die:
        return h_vol, R_vol, R_die is None and False or (R_die is None)
    return 2.0 * np.pi * tau_y * R_die**3 / (3.0 * F0), R_die, True


def bingham_critical_yield_stress(F0, V0: float, R_die: float):
    r"""Critical yield stress tau_y,crit at which h*_vol == h_c = V0/(pi R_die^2)
    (equivalently R* == R_die):

        tau_y,crit = 3 F0 h_c / (2 pi R_die^3) = 3 F0 V0 / (2 pi^2 R_die^5).

    For tau_y <= tau_y,crit the paste reaches full die coverage before stalling;
    for tau_y > tau_y,crit it stalls in the constant-volume phase with R* < R_die.
    """
    hc = cap_thickness(V0, R_die)
    return 3.0 * np.asarray(F0, dtype=float) * hc / (2.0 * np.pi * R_die**3)


def bingham_critical_force(tau_y, V0: float, R_die: float):
    r"""Minimum clamping force F_crit(tau_y) required to reach full die coverage R* = R_die:

        F_crit(tau_y) = 2 pi R_die^3 tau_y / (3 h_c) = 2 pi^2 R_die^5 tau_y / (3 V0).
    """
    hc = cap_thickness(V0, R_die)
    return 2.0 * np.pi * R_die**3 * np.asarray(tau_y, dtype=float) / (3.0 * hc)


def bingham_rate(h, F0: float, fluid: Bingham, V0: float, R_die=None):
    """Squeeze rate W(h) for a Bingham fluid; W = 0 once h <= h*."""
    h = np.atleast_1d(np.asarray(h, dtype=float))
    if fluid.tau_y <= 0.0:
        return newtonian_rate(h, F0, fluid.mu_p, V0, R_die)
    R = wetted_radius(h, V0, R_die)
    target = 3.0 * F0 * h / (2.0 * np.pi * fluid.tau_y * R**3)
    W = np.zeros_like(h)
    moving = target > 1.0
    if np.any(moving):
        Lam = _invert_Phi(target[moving])
        W[moving] = Lam * fluid.tau_y * h[moving] ** 2 / (3.0 * fluid.mu_p * R[moving])
    return W


@dataclass
class BinghamSolution:
    r"""Semi-analytical h(t) for constant-force Bingham squeeze flow.

    Instead of time-stepping, the solution is parametrised by Lambda:
    for each Lambda, Phi(Lambda) fixes h through the force balance
    ``3 F0 h / (2 pi tau_y R(h)^3) = Phi``  (closed-form inversion of R(h)),
    then ``W = Lambda tau_y h^2 / (3 mu_p R)`` and
    ``t(h) = \int_h^{h0} dh'/W(h')`` by trapezoidal quadrature.
    h -> h* only as t -> infinity (h* - h ~ 1/t).
    """
    fluid: Bingham
    F0: float
    V0: float
    h0: float
    R_die: Optional[float] = None
    n_grid: int = 20000
    t_grid: np.ndarray = field(init=False, repr=False)
    h_grid: np.ndarray = field(init=False, repr=False)
    W_grid: np.ndarray = field(init=False, repr=False)

    def __post_init__(self):
        b, F0, V0 = self.fluid, self.F0, self.V0
        self.h_star, self.R_star, self.covers_die = bingham_stall(F0, b.tau_y, V0, self.R_die)
        hc = cap_thickness(V0, self.R_die)

        if self.h0 <= self.h_star:          # never yields
            self.t_grid = np.array([0.0, np.inf])
            self.h_grid = np.array([self.h0, self.h0])
            self.W_grid = np.zeros(2)
            return

        def h_of_target(T):
            # target(h) = 3 F0 h / (2 pi tau_y R(h)^3), monotone increasing in h
            cv = 3.0 * F0 * np.pi**1.5 / (2.0 * np.pi * b.tau_y * V0**1.5)  # vol phase: cv h^2.5
            T_c = cv * hc**2.5 if hc > 0 else 0.0
            h_vol = (T / cv) ** 0.4
            if self.R_die is None:
                return h_vol
            h_area = T * 2.0 * np.pi * b.tau_y * self.R_die**3 / (3.0 * F0)
            return np.where(T > T_c, h_vol, h_area)

        R0 = wetted_radius(self.h0, V0, self.R_die)
        Lam0 = _invert_Phi(3.0 * F0 * self.h0 / (2.0 * np.pi * b.tau_y * R0**3))[0]
        Lam = np.logspace(np.log10(Lam0), np.log10(Lam0) - 24.0, self.n_grid)
        h = h_of_target(bingham_Phi(Lam))
        h[0] = self.h0
        R = wetted_radius(h, V0, self.R_die)
        W = Lam * b.tau_y * h**2 / (3.0 * b.mu_p * R)
        dt = 0.5 * (1.0 / W[1:] + 1.0 / W[:-1]) * (h[:-1] - h[1:])
        self.t_grid = np.concatenate([[0.0], np.cumsum(dt)])
        self.h_grid, self.W_grid = h, W

    def h(self, t):
        t = np.asarray(t, dtype=float)
        return np.where(t > self.t_grid[-1], self.h_star,
                        np.interp(t, self.t_grid, self.h_grid))

    def rate(self, t):
        """W(t) re-evaluated *exactly* from the force balance at h(t), so that
        F(h, R, W) = F0 holds to solver precision at every output time."""
        h = np.atleast_1d(self.h(t))
        W = bingham_rate(h, self.F0, self.fluid, self.V0, self.R_die)
        return W.reshape(np.shape(t))


# =========================================================================== #
# Generic dispatch
# =========================================================================== #
def squeeze_force(h, R, W, fluid: Fluid):
    """F(h, R, W) for any supported fluid."""
    if isinstance(fluid, Newtonian):
        return newtonian_force(h, R, W, fluid.mu)
    if isinstance(fluid, PowerLaw):
        return power_law_force(h, R, W, fluid.K, fluid.n)
    if isinstance(fluid, Bingham):
        return bingham_force(h, R, W, fluid.mu_p, fluid.tau_y)
    raise TypeError(f"unsupported fluid {fluid!r}")


def squeeze_rate(h, fluid: Fluid, F0: float, V0: float, R_die=None):
    """W(h) = -dh/dt from the force balance F(h, R(h), W) = F0."""
    if isinstance(fluid, Newtonian):
        return newtonian_rate(h, F0, fluid.mu, V0, R_die)
    if isinstance(fluid, PowerLaw):
        return power_law_rate(h, F0, fluid.K, fluid.n, V0, R_die)
    if isinstance(fluid, Bingham):
        return bingham_rate(h, F0, fluid, V0, R_die)
    raise TypeError(f"unsupported fluid {fluid!r}")


@dataclass
class SqueezeResult:
    """Time history of a constant-force squeeze."""
    fluid: Fluid
    t: np.ndarray
    h: np.ndarray
    R: np.ndarray
    W: np.ndarray             # -dh/dt  [m/s]
    R_die: Optional[float]
    V0: float
    h_star: float = 0.0
    R_star: float = np.inf

    @property
    def coverage(self):
        """Wetted fraction of the (equivalent-disk) die area."""
        if self.R_die is None:
            return np.ones_like(self.R)
        return np.minimum(self.R / self.R_die, 1.0) ** 2


def solve_squeeze(fluid: Fluid, t, F0: float, V0: float, h0: float, R_die=None) -> SqueezeResult:
    """Unified constant-force, constant-volume, die-capped squeeze solver."""
    t = np.asarray(t, dtype=float)
    h_star, R_star = 0.0, (R_die if R_die is not None else np.inf)
    if isinstance(fluid, Newtonian):
        h = newtonian_h(t, F0, fluid.mu, V0, h0, R_die)
        W = newtonian_rate(h, F0, fluid.mu, V0, R_die)
    elif isinstance(fluid, PowerLaw):
        h = power_law_h(t, fluid, F0, V0, h0, R_die)
        W = power_law_rate(h, F0, fluid.K, fluid.n, V0, R_die)
    elif isinstance(fluid, Bingham):
        if fluid.tau_y <= 0.0:
            h = newtonian_h(t, F0, fluid.mu_p, V0, h0, R_die)
            W = newtonian_rate(h, F0, fluid.mu_p, V0, R_die)
        else:
            sol = BinghamSolution(fluid, F0, V0, h0, R_die)
            h, W = sol.h(t), sol.rate(t)
            h_star, R_star = sol.h_star, sol.R_star
    else:
        raise TypeError(f"unsupported fluid {fluid!r}")
    R = wetted_radius(h, V0, R_die)
    return SqueezeResult(fluid, t, h, R, W, R_die, V0, h_star, R_star)


# =========================================================================== #
# Local fields at an instant (h, W given):  G(r), p(r), u_r(r,z), tau_rz(r,z)
# =========================================================================== #
def pressure_gradient(r, h: float, W: float, fluid: Fluid):
    """G(r) = -dp/dr  [Pa/m]."""
    r = np.asarray(r, dtype=float)
    if isinstance(fluid, Newtonian):
        return 6.0 * fluid.mu * r * W / h**3
    if isinstance(fluid, PowerLaw):
        n = fluid.n
        return 2.0 * fluid.K * _pl_coeff(n) * (W * r) ** n / h ** (2.0 * n + 1.0)
    if isinstance(fluid, Bingham):
        if fluid.tau_y <= 0.0:
            return 6.0 * fluid.mu_p * r * W / h**3
        xi = bingham_plug_fraction(3.0 * fluid.mu_p * r * W / (fluid.tau_y * h**2))
        return 2.0 * fluid.tau_y / (h * xi)
    raise TypeError(f"unsupported fluid {fluid!r}")


def pressure(r, h: float, R: float, W: float, fluid: Fluid):
    """Gauge pressure p(r) - p_inf with p(R) = 0  [Pa] (zero for r > R)."""
    r = np.asarray(r, dtype=float)
    rr = np.minimum(r, R)
    if isinstance(fluid, Newtonian) or (isinstance(fluid, Bingham) and fluid.tau_y <= 0.0):
        mu = fluid.mu if isinstance(fluid, Newtonian) else fluid.mu_p
        p = 3.0 * mu * W * (R**2 - rr**2) / h**3
    elif isinstance(fluid, PowerLaw):
        n = fluid.n
        C = 2.0 * fluid.K * _pl_coeff(n) * W**n / h ** (2.0 * n + 1.0)
        p = C * (R ** (n + 1.0) - rr ** (n + 1.0)) / (n + 1.0)
    elif isinstance(fluid, Bingham):
        # p = (2 tau_y R / h) * Lambda^-1 * [Kf(xi(Lambda)) - Kf(xi(Lambda s))]
        # with Kf(xi) = (1-xi)^2 (1+2xi) / (2 xi^2) (cancellation-free form).
        Lam = 3.0 * fluid.mu_p * R * W / (fluid.tau_y * h**2)
        if Lam < 1e-12:                                   # plastic limit
            p = 2.0 * fluid.tau_y * (R - rr) / h
        else:
            # Kf written in delta = 1 - xi:  delta^2 (3 - 2 delta) / (2 (1-delta)^2)
            Kf = lambda d: d * d * (3.0 - 2.0 * d) / (2.0 * (1.0 - d) ** 2)
            d_R = bingham_yield_fraction(Lam)
            d_r = bingham_yield_fraction(Lam * rr / R)
            p = 2.0 * fluid.tau_y * R / h * (Kf(d_R) - Kf(d_r)) / Lam
    else:
        raise TypeError(f"unsupported fluid {fluid!r}")
    return np.where(r > R, 0.0, p)


def plug_half_thickness(r, h: float, W: float, fluid: Bingham):
    """Bingham (pseudo-)plug half-thickness z0(r) = tau_y / G(r) = xi0 h / 2."""
    if not isinstance(fluid, Bingham) or fluid.tau_y <= 0.0:
        return np.zeros_like(np.asarray(r, dtype=float))
    return fluid.tau_y / pressure_gradient(r, h, W, fluid)


def velocity(r, z, h: float, W: float, fluid: Fluid):
    """Radial velocity u_r(r, z) [m/s], z in [0, h], no-slip at both plates."""
    r, z = np.broadcast_arrays(np.asarray(r, float), np.asarray(z, float))
    G = pressure_gradient(r, h, W, fluid)
    zeta = np.abs(z - 0.5 * h)
    H = 0.5 * h
    if isinstance(fluid, Newtonian) or (isinstance(fluid, Bingham) and fluid.tau_y <= 0.0):
        mu = fluid.mu if isinstance(fluid, Newtonian) else fluid.mu_p
        return G / (2.0 * mu) * (H**2 - zeta**2)
    if isinstance(fluid, PowerLaw):
        n = fluid.n
        e = (n + 1.0) / n
        return (G / fluid.K) ** (1.0 / n) * n / (n + 1.0) * (H**e - zeta**e)
    if isinstance(fluid, Bingham):
        z0 = fluid.tau_y / np.maximum(G, _TINY)
        zz = np.maximum(zeta, z0)                         # plug moves rigidly
        return G / (2.0 * fluid.mu_p) * (H**2 - zz**2) - fluid.tau_y / fluid.mu_p * (H - zz)
    raise TypeError(f"unsupported fluid {fluid!r}")


def shear_stress(r, z, h: float, W: float, fluid: Fluid):
    r"""tau_rz(r, z) = -G(r) (z - h/2)  -- linear for *every* fluid.

    Inside the Bingham pseudo-plug |tau_rz| < tau_y; the lubrication solution
    is nonetheless kinematically inconsistent there because the plug speed
    varies with r (Lipscomb-Denn paradox) -- see the notebook.
    """
    r, z = np.broadcast_arrays(np.asarray(r, float), np.asarray(z, float))
    return -pressure_gradient(r, h, W, fluid) * (z - 0.5 * h)

r"""
diagnostics.py -- Component 4: Dimensional analysis & physics verification.

Two jobs:

1. **Assumption-validity trackers** (Buckingham-pi groups along a trajectory)

   * aspect ratio           eps(t)   = h / R                      (lubrication: << 1)
   * squeeze Reynolds       Re_sq(t) = rho |dh/dt| h / mu_eff      (creeping:    << 1)
   * Bingham number         Bn(t)    = tau_y h^2 / (mu_p R |dh/dt|) (-> inf at stall)

   with the characteristic wall shear rate gamma_c = R |dh/dt| / h^2 and
   mu_eff = K gamma_c^{n-1} (power law), mu_p + tau_y/gamma_c (Bingham).

2. **Automated limiting-case & conservation checks** -- each returns a
   :class:`Check` (name, measured error, tolerance, pass/fail).  They are run
   by ``verify_physics.py`` and the notebook.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, List

import numpy as np

import rheology_models as rm
import thermal_coupling as tc
from params import (BINGHAM, DROPLET, GPU_700W, NEWTONIAN, SHEAR_THICKENING,
                    SHEAR_THINNING, THERMAL, Bingham, Fluid, Newtonian, PowerLaw)

__all__ = [
    "aspect_ratio", "characteristic_shear_rate", "effective_viscosity",
    "squeeze_reynolds", "bingham_number", "validity_report",
    "Check", "ALL_CHECKS", "run_all_checks", "format_checks",
]


# =========================================================================== #
# 1. Dimensionless groups
# =========================================================================== #
def aspect_ratio(h, R):
    """eps = h / R."""
    return np.asarray(h, float) / np.asarray(R, float)


def characteristic_shear_rate(h, R, W):
    """gamma_c = R W / h^2 (wall shear rate at the rim, up to an O(1) factor)."""
    return np.asarray(R, float) * np.asarray(W, float) / np.asarray(h, float) ** 2


def effective_viscosity(fluid: Fluid, h, R, W):
    """Apparent viscosity evaluated at gamma_c  [Pa s]."""
    g = np.maximum(characteristic_shear_rate(h, R, W), 1e-300)
    if isinstance(fluid, Newtonian):
        return np.full_like(g, fluid.mu)
    if isinstance(fluid, PowerLaw):
        return fluid.K * g ** (fluid.n - 1.0)
    if isinstance(fluid, Bingham):
        return fluid.mu_p + fluid.tau_y / g
    raise TypeError(fluid)


def squeeze_reynolds(fluid: Fluid, h, R, W):
    """Re_sq = rho W h / mu_eff."""
    return fluid.rho * np.asarray(W, float) * np.asarray(h, float) / effective_viscosity(fluid, h, R, W)


def bingham_number(fluid: Fluid, h, R, W):
    """Bn = tau_y h^2 / (mu_p R W)  (0 for non-yield-stress fluids)."""
    if not isinstance(fluid, Bingham):
        return np.zeros_like(np.asarray(h, float))
    W = np.maximum(np.asarray(W, float), 1e-300)
    return fluid.tau_y * np.asarray(h, float) ** 2 / (fluid.mu_p * np.asarray(R, float) * W)


def validity_report(res: rm.SqueezeResult) -> dict:
    """Dimensionless-group histories for a :class:`SqueezeResult`."""
    moving = res.W > 0
    out = {
        "eps": aspect_ratio(res.h, res.R),
        "Re_sq": np.where(moving, squeeze_reynolds(res.fluid, res.h, res.R, res.W), 0.0),
        "Bn": bingham_number(res.fluid, res.h, res.R, res.W),
    }
    out["max_eps"] = float(np.max(out["eps"]))
    out["max_Re_sq"] = float(np.max(out["Re_sq"]))
    return out


# =========================================================================== #
# 2. Verification checks
# =========================================================================== #
@dataclass
class Check:
    name: str
    error: float
    tol: float
    detail: str = ""

    @property
    def passed(self) -> bool:
        return bool(np.isfinite(self.error) and self.error <= self.tol)


def _rel(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1e-300)))


def _trapz(y, x):
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x)))


G, D = GPU_700W, DROPLET
T_TEST = np.concatenate([[0.0], np.logspace(-4, 2, 200)])


def check_powerlaw_n1_equals_newtonian() -> Check:
    """Check 1: power law with n = 1, K = mu reproduces Stefan's solution."""
    mu = NEWTONIAN.mu
    pl = PowerLaw(K=mu, n=1.0)
    hN = rm.newtonian_h(T_TEST, G.F0, mu, D.V0, D.h0, G.R_die)
    hP = rm.power_law_h(T_TEST, pl, G.F0, D.V0, D.h0, G.R_die)
    err = _rel(hP, hN)
    h, R = 1e-4, rm.wetted_radius(1e-4, D.V0, G.R_die)
    W = rm.newtonian_rate(h, G.F0, mu, D.V0, G.R_die)
    r = np.linspace(0, R, 101)
    z = np.linspace(0, h, 51)[:, None]
    err = max(err,
              _rel(rm.pressure(r[:-1], h, R, W, pl), rm.pressure(r[:-1], h, R, W, NEWTONIAN)),
              _rel(rm.velocity(r[1:], z[1:-1], h, W, pl), rm.velocity(r[1:], z[1:-1], h, W, NEWTONIAN)),
              _rel(rm.power_law_rate(h, G.F0, mu, 1.0, D.V0, G.R_die), W))
    return Check("Power-law (n=1, K=mu) == Newtonian  [h(t), p(r), u_r(r,z), dh/dt]", err, 1e-12)


def check_bingham_zero_yield() -> Check:
    """Check 2a: Bingham with tau_y -> 0 recovers Newtonian."""
    b = Bingham(mu_p=NEWTONIAN.mu, tau_y=1e-3)
    hN = rm.newtonian_h(T_TEST, G.F0, NEWTONIAN.mu, D.V0, D.h0, G.R_die)
    hB = rm.solve_squeeze(b, T_TEST, G.F0, D.V0, D.h0, G.R_die).h
    err = _rel(hB, hN)
    h, R = 2e-4, rm.wetted_radius(2e-4, D.V0, G.R_die)
    W = rm.newtonian_rate(h, G.F0, NEWTONIAN.mu, D.V0, G.R_die)
    r = np.linspace(0, R, 101)[:-1]
    err = max(err,
              _rel(rm.pressure(r, h, R, W, b), rm.pressure(r, h, R, W, NEWTONIAN)),
              _rel(rm.bingham_rate(h, G.F0, b, D.V0, G.R_die), W))
    return Check("Bingham (tau_y = 1e-3 Pa) -> Newtonian  [h(t), p(r), dh/dt]", err, 1e-4)


def check_bingham_stall() -> List[Check]:
    """Check 2b: h(t -> inf) -> h* (plastic limit), both stall regimes."""
    out = []
    for tau in (BINGHAM.tau_y, 5000.0):
        b = replace(BINGHAM, tau_y=tau)
        sol = rm.BinghamSolution(b, G.F0, D.V0, D.h0, G.R_die)
        h_inf = float(sol.h(1e12))
        regime = "die covered, constant-area stall" if sol.covers_die else "UNDER-COVERAGE, constant-volume stall"
        out.append(Check(f"Bingham tau_y={tau:g} Pa: h(t->inf) -> h* = {sol.h_star*1e6:.2f} um ({regime})",
                         abs(h_inf / sol.h_star - 1.0), 1e-3))
        # plastic-limit force with h* must equal F0 exactly
        F_pl = 2 * np.pi * tau * sol.R_star**3 / (3 * sol.h_star)
        out.append(Check(f"Bingham tau_y={tau:g} Pa: plastic-limit force at h* == F0",
                         abs(F_pl / G.F0 - 1.0), 1e-12))
    return out


def _fluids():
    return [NEWTONIAN, SHEAR_THINNING, SHEAR_THICKENING, BINGHAM, replace(BINGHAM, tau_y=5000.0)]


def check_volume_conservation() -> Check:
    """Check 3a: pi R^2 h = V0 in the constant-volume phase, <= V0 after capping."""
    err = 0.0
    for f in _fluids():
        res = rm.solve_squeeze(f, T_TEST, G.F0, D.V0, D.h0, G.R_die)
        V = np.pi * res.R**2 * res.h
        free = res.R < G.R_die * (1 - 1e-12)
        if np.any(free):
            err = max(err, _rel(V[free], D.V0))
        if np.any(~free):
            err = max(err, float(np.max(np.maximum(V[~free] / D.V0 - 1.0, 0.0))))
    return Check("Volume conservation pi R(t)^2 h(t) = V0 (all fluids, every step)", err, 1e-12)


def check_force_balance() -> Check:
    """Check 3b: integral_0^R p 2 pi r dr = F0 along every trajectory."""
    err = 0.0
    t_sample = np.array([1e-3, 0.1, 1.0, 10.0, 60.0])
    for f in _fluids():
        res = rm.solve_squeeze(f, t_sample, G.F0, D.V0, D.h0, G.R_die)
        for h, R, W in zip(res.h, res.R, res.W):
            if W <= 0:
                continue
            # tanh-clustered grid toward r = R resolves the rim
            r = R * np.sin(0.5 * np.pi * np.linspace(0, 1, 20001))
            F = _trapz(rm.pressure(r, h, R, W, f) * 2 * np.pi * r, r)
            err = max(err, abs(F / G.F0 - 1.0))
    return Check("Force balance  int_0^R p 2 pi r dr = F0 (all fluids, sampled steps)", err, 1e-6)


def check_flux_continuity() -> Check:
    """Continuity: int_0^h u_r dz = r W / 2 at every radius."""
    err = 0.0
    h = 5e-5
    zg = np.polynomial.legendre.leggauss(80)
    for f in _fluids():
        R = rm.wetted_radius(h, D.V0, G.R_die)
        W = float(np.atleast_1d(rm.squeeze_rate(h, f, G.F0, D.V0, G.R_die))[0])
        if W <= 0:
            continue
        r = np.linspace(0.05, 1.0, 20) * R
        # composite Gauss over sub-intervals handles the plug-edge kink
        z = np.linspace(0, h, 401)
        q = np.zeros_like(r)
        for a, b in zip(z[:-1], z[1:]):
            zz = 0.5 * (b - a) * zg[0] + 0.5 * (a + b)
            q += 0.5 * (b - a) * (rm.velocity(r[:, None], zz[None, :], h, W, f) @ zg[1])
        err = max(err, _rel(q, r * W / 2))
    return Check("Continuity  int_0^h u_r dz = r(-dh/dt)/2 (all fluids)", err, 1e-6)


def check_bingham_plug() -> Check:
    """Constitutive: |tau_rz| <= tau_y exactly inside the plug, u_r flat there."""
    b = BINGHAM
    h = 3e-5
    R = rm.wetted_radius(h, D.V0, G.R_die)
    W = float(rm.bingham_rate(h, G.F0, b, D.V0, G.R_die)[0])
    r = np.linspace(0.01, 1, 50) * R
    z0 = rm.plug_half_thickness(r, h, W, b)
    zp = 0.5 * h + z0 * 0.999
    tau = np.abs(rm.shear_stress(r, zp, h, W, b))
    u_mid = rm.velocity(r, 0.5 * h, h, W, b)
    u_edge = rm.velocity(r, 0.5 * h + z0, h, W, b)
    err = max(float(np.max(np.maximum(tau / b.tau_y - 1.0, 0.0))), _rel(u_edge, u_mid))
    S = np.logspace(-14, 14, 300)
    xi = rm.bingham_plug_fraction(S)
    err = max(err, float(np.max(np.abs(xi**3 - (3 + 2 * S) * xi + 2) / (2 + (3 + 2 * S) * xi))))
    return Check("Bingham plug: |tau_rz| <= tau_y in core, rigid core, exact cubic root", err, 1e-9)


def check_scaling_exponents() -> List[Check]:
    """Late-time slopes in the constant-volume phase: h ~ t^{-2n/(3n+5)}."""
    out = []
    t = np.array([1e6, 1e7])
    for f, n in [(NEWTONIAN, 1.0), (SHEAR_THINNING, SHEAR_THINNING.n), (SHEAR_THICKENING, SHEAR_THICKENING.n)]:
        h = rm.solve_squeeze(f, t, G.F0, D.V0, D.h0, R_die=None).h
        slope = np.log(h[1] / h[0]) / np.log(t[1] / t[0])
        expected = -2 * n / (3 * n + 5)
        out.append(Check(f"Scaling h ~ t^(-2n/(3n+5)), n={n:g}: slope {slope:.5f} vs {expected:.5f}",
                         abs(slope / expected - 1.0), 1e-3))
    return out


def check_dimensional_homogeneity() -> Check:
    """Change of units (L -> L/lambda, M -> M/m, T -> T/s) must leave physics invariant."""
    lam, m, s = 1e3, 7.0, 0.01                    # metres->mm, arbitrary mass & time units
    t = np.array([0.0, 0.5, 5.0, 50.0])
    err = 0.0
    for f in _fluids():
        if isinstance(f, Newtonian):
            g = Newtonian(mu=f.mu * m / (lam * s), rho=f.rho)
        elif isinstance(f, PowerLaw):
            g = PowerLaw(K=f.K * m * s ** (f.n - 2) / lam, n=f.n, rho=f.rho)
        else:
            g = Bingham(mu_p=f.mu_p * m / (lam * s), tau_y=f.tau_y * m / (lam * s**2), rho=f.rho)
        h1 = rm.solve_squeeze(f, t, G.F0, D.V0, D.h0, G.R_die).h
        h2 = rm.solve_squeeze(g, t * s, G.F0 * m * lam / s**2, D.V0 * lam**3, D.h0 * lam, G.R_die * lam).h
        err = max(err, _rel(h2 / lam, h1))
    return Check("Dimensional homogeneity: h(t) invariant under change of units (M, L, T)", err, 1e-6)


def check_thermal_limits() -> Check:
    """Thermal network limits: full coverage -> h/(k A); no coverage -> air only."""
    h = np.array([1e-5, 5e-5])
    e1 = _rel(tc.tim_resistance(h, G.R_die), h / (THERMAL.k_tim * G.A_die))
    e2 = _rel(tc.tim_resistance(h, 1e-12), h / (THERMAL.k_air * G.A_die))
    return Check("Thermal network limits (full coverage, zero coverage)", max(e1, e2), 1e-9)


def check_bingham_critical_yield_stress() -> Check:
    """Issue 1 check: tau_y,crit == 3 F0 h_c / (2 pi R_die^3) and h*_vol(tau_y,crit) == h_c."""
    hc = rm.cap_thickness(D.V0, G.R_die)
    tau_crit = float(rm.bingham_critical_yield_stress(G.F0, D.V0, G.R_die))
    expected = 3.0 * G.F0 * hc / (2.0 * np.pi * G.R_die**3)
    h_vol_crit, R_vol_crit, _ = rm.bingham_stall(G.F0, tau_crit, D.V0, R_die=None)
    _, _, cov_250 = rm.bingham_stall(G.F0, 250.0, D.V0, G.R_die)
    _, _, cov_5k = rm.bingham_stall(G.F0, 5000.0, D.V0, G.R_die)
    side_err = 0.0 if (cov_250 and not cov_5k and 250.0 < tau_crit < 5000.0) else 1.0
    err = max(abs(tau_crit / expected - 1.0), abs(h_vol_crit / hc - 1.0),
              abs(R_vol_crit / G.R_die - 1.0), side_err)
    return Check(
        f"Critical yield stress tau_y,crit = 3 F0 h_c / (2 pi R_die^3) = {tau_crit:.1f} Pa & h*_vol(tau_y,crit) == h_c",
        err, 1e-9,
    )


def _rk4_integrate_rate(rate_fn, h0: float, t_end: float, t_c: float = 0.0, n_steps: int = 800) -> float:
    """Classical 4th-order Runge-Kutta integration of dh/dt = -rate_fn(h)
    using log-spaced time intervals (clustered at early times where W(h0) is large)
    and split exactly at the Phase-1 -> Phase-2 transition time t_c."""
    t_piv = t_c if 0.0 < t_c < t_end else 1.0
    t_early = np.concatenate([[0.0], np.logspace(-9, np.log10(t_piv), n_steps // 2)])
    t_late = np.linspace(t_piv, t_end, n_steps // 2 + 1)[1:]
    t_grid = np.concatenate([t_early, t_late])
    h = float(h0)
    for dt in np.diff(t_grid):
        k1 = -float(rate_fn(h))
        k2 = -float(rate_fn(h + 0.5 * dt * k1))
        k3 = -float(rate_fn(h + 0.5 * dt * k2))
        k4 = -float(rate_fn(h + dt * k3))
        h += (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    return h


def check_powerlaw_ode_vs_closed_form() -> List[Check]:
    """Issue 2 regression check: ODE integration of Scott's law matches closed-form
    power_law_h for n in {0.5, 1.0, 1.3} at t = 60 s within 1e-6."""
    out: List[Check] = []
    hc = rm.cap_thickness(D.V0, G.R_die)
    for n_val in (0.5, 1.0, 1.3):
        fl = PowerLaw(K=100.0, n=n_val)
        c = ((2.0 * n_val + 1.0) / n_val) ** n_val
        m = (5.0 * n_val + 5.0) / (2.0 * n_val)
        A = ((G.F0 * (n_val + 3.0) / (2.0 * np.pi * fl.K * c)) ** (1.0 / n_val)
             * (np.pi / D.V0) ** ((n_val + 3.0) / (2.0 * n_val)))
        t_c = float((hc ** (1.0 - m) - D.h0 ** (1.0 - m)) / ((m - 1.0) * A))
        h_closed = float(rm.power_law_h(60.0, fl, G.F0, D.V0, D.h0, G.R_die))
        h_ode = _rk4_integrate_rate(
            lambda hh, f=fl: rm.power_law_rate(hh, G.F0, f.K, f.n, D.V0, G.R_die),
            D.h0, 60.0, t_c=t_c, n_steps=4000,
        )
        err = abs(h_ode - h_closed) / h_closed
        out.append(Check(
            f"Power-law ODE vs. closed-form h(60 s) for n={n_val:g}: {h_closed*1e6:.2f} um",
            err, 1e-6,
        ))
    return out


def check_bingham_ordering_vs_newtonian() -> Check:
    """Issue 3 check: for every time t, h_Bingham(t) >= h_Newtonian(t) when mu_p == mu,
    and h_Bingham(t) >= h*_area."""
    hN = rm.newtonian_h(T_TEST, G.F0, NEWTONIAN.mu, D.V0, D.h0, G.R_die)
    err = 0.0
    for tau in (BINGHAM.tau_y, 5000.0):
        b = Bingham(mu_p=NEWTONIAN.mu, tau_y=tau)
        resB = rm.solve_squeeze(b, T_TEST, G.F0, D.V0, D.h0, G.R_die)
        viol_newt = float(np.max(np.maximum((hN - resB.h) / hN, 0.0)))
        viol_stall = float(np.max(np.maximum((resB.h_star - resB.h) / resB.h_star, 0.0)))
        err = max(err, viol_newt, viol_stall)
    return Check(
        "Bingham ordering: h_Bingham(t) >= h_Newtonian(t) (mu_p=mu) and h_Bingham(t) >= h* for all t",
        err, 1e-12,
    )


ALL_CHECKS: List[Callable] = [
    check_powerlaw_n1_equals_newtonian,
    check_bingham_zero_yield,
    check_bingham_stall,
    check_bingham_critical_yield_stress,
    check_powerlaw_ode_vs_closed_form,
    check_bingham_ordering_vs_newtonian,
    check_volume_conservation,
    check_force_balance,
    check_flux_continuity,
    check_bingham_plug,
    check_scaling_exponents,
    check_dimensional_homogeneity,
    check_thermal_limits,
]


def run_all_checks() -> List[Check]:
    out: List[Check] = []
    for fn in ALL_CHECKS:
        r = fn()
        out.extend(r if isinstance(r, list) else [r])
    return out


def format_checks(checks: List[Check]) -> str:
    lines = [f"{'#':>2}  {'status':6}  {'error':>10}  {'tol':>8}  check", "-" * 100]
    for i, c in enumerate(checks, 1):
        lines.append(f"{i:>2}  {'PASS' if c.passed else 'FAIL':6}  {c.error:10.2e}  {c.tol:8.0e}  {c.name}")
    n = sum(c.passed for c in checks)
    lines += ["-" * 100, f"{n}/{len(checks)} checks passed"]
    return "\n".join(lines)

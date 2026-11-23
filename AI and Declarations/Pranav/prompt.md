# Project prompt: squeeze flow of thermal paste, with a thermal-resistance map

You are helping a 3rd-semester undergraduate (Materials Science and Metallurgical Engineering) with a graded course project in *Transport Phenomena in Materials Processing*. The course covered: continuity equation and Reynolds transport theorem (RTT) on control volumes, the constant-property incompressible Newtonian Navier-Stokes equation, Couette flow, force balance on a control volume, Reynolds number, dimensional analysis and Buckingham's theorem, similarity solutions, Fourier number, Biot number, thermal resistance. Do not use theory beyond this without deriving it from these tools and defining every new term inline.

## 1. Professor's brief (verbatim)

"Explain how squeezing a viscous paste between flat surfaces changes its pressure, flow and resisting force. Develop one simple baseline model, state its assumptions and compare at least three gaps or approach speeds. Connect layer thickness to thermal resistance. Check the flow or force result independently and state what the model omits."

## 2. What to build

A Python program (NumPy/SciPy; interactive part with matplotlib mouse events) plus a short report-ready results package.

**Setup:** a horizontal square plate of controllable area; a uniform areal force P (N/m², controllable) applied by a rigid parallel plate that stays parallel at all times; thermal paste applied by the user in an arbitrary shape (click = apply a dot, hold = continuous extrusion, drag = vary the initial spread; make application realistic since it sets the initial condition). Controllable paste parameters: constant Newtonian viscosity μ and thermal resistivity r only. Paste that leaves the plate area is discarded (log its volume, then forget it). After the force period ends, a chip heat source switches on and the program shows the temperature field.

**Defaults (all user-adjustable except where noted):** plate 40 mm x 40 mm; total force 50 N (about 31 kPa); effective μ = 100 Pa s; r = 0.2 m K/W (k = 5 W/m K); fixed minimum gap h_min = 20 um (stand-in for filler particle size, not user-controlled).

## 3. Physics (derive, do not just quote)

Notation: plates at z = 0 and z = h(t); approach speed U = -dh/dt; p = gauge pressure; q = volume flow per unit width; F = P x plate area.

1. **Reduce momentum.** Thin gap (h << lateral size L): shear across the gap dominates, so p depends only on (x, y). Inertia/viscous ratio = rho U h^2/(mu L) = Re_h (h/L), with Re_h = rho U h/mu; the time term is dropped because t_nu = h^2/nu is far shorter than the time over which h changes; gravity changes p across the gap by rho g h, negligible. Result: 0 = -dp/dx + mu d2u/dz2 (same for y).
2. **Integrate with no-slip at both plates:** parabolic profile u = -(1/2mu)(dp/dx) z(h - z). Flow per unit width: q = -(h^3/12mu) grad p. Explain how this relates to Couette flow (Couette: moving wall, linear profile; here: fixed walls, pressure-driven).
3. **Continuity on a column control volume (RTT):** div q = U.
4. **Combine:** laplacian(p) = -12 mu U / h^3, p = 0 at the free paste edge. Point out the isomorphism with steady heat conduction with uniform source: p <-> T, 12 mu U/h^3 <-> q/k.
5. **Force balance:** P x A_plate = integral of p over the paste footprint. Linearity: p = U p_hat, so U = F / integral(p_hat dA) with no iteration.

**Closed forms for validation (equal-area disc, radius R):**
- Full disc: p = 3 mu U (R^2 - r^2)/h^3; F = 3 pi mu U R^4/(2 h^3); constant-F: h^-2 = h0^-2 + 4 F t/(3 pi mu R^4).
- Partial-fill circular blob of volume Vol (before it reaches the plate edge): R^2 = Vol/(pi h); F = 3 mu U Vol^2/(2 pi h^5); constant-F: h^-4 = h0^-4 + 8 pi F t/(3 mu Vol^2). Force slope vs h is -5 on a log-log plot, switching to -3 once the paste fills the plate.
- Dimensional analysis: F h^3/(mu U R^4) is dimensionless; the solution fixes it at 3pi/2 (disc). Show how this follows from scale analysis and Buckingham's theorem.

**Reference numbers (equal-area disc, R = 22.57 mm, mu = 100 Pa s, F = 50 N, h0 = 300 um; recompute and verify, do not trust blindly):** time to reach 200 / 100 / 50 um is about 17 s / 109 s / 475 s. At fixed U = 1e-5 m/s the force at 200 / 100 / 50 um is about 0.15 N / 1.2 N / 9.8 N.

## 4. Assumptions to state in the report (course terms only)

Fluid: constant-property incompressible Newtonian paste; single homogeneous phase (no fillers); no-slip on both plates.
Flow: gap << lateral size; p independent of z; inertia, time derivative, gravity dropped (give the numerical estimates); paste touches both plates everywhere in its footprint.
Plate/force: rigid, flat, horizontal, parallel at all times; plate inertia neglected (instantaneous force balance); plate weight included in F; torque ignored (an off-centre blob would tilt a real plate; the parallel constraint hides this).
Boundary: p = 0 (gauge) at the paste/air edge; surface tension and wetting neglected (estimate capillary pressure ~ gamma/h and report it); front moves with the depth-averaged velocity; paste crossing the plate boundary is deleted.
Initial condition ("pancake rule"): the user's deposit map s(x,y) is converted to a uniform-thickness pancake whose footprint is the support of s and whose thickness is h0 = Vol/footprint area (mean thickness); volume is conserved; early partial contact with dome tops is ignored (state this as a break point). When the force switches off, p = 0 and flow stops immediately (no inertia, no elastic recoil), so the shape freezes.
Thermal: steady state; constant properties; no heat generation in the paste; 1D heat flow across the thin paste layer with resistance per unit area r*h; dry (air) regions have conductance k_air/h with k_air = 0.026 W/m K; plates treated as thin sheets (temperature varies in x, y only) and the Biot number must be checked and reported (Bi = G t/k; for 3 mm copper it is about 0.4, above 0.1, so absolute temperature differences carry an error of order Bi); no contact resistance; no edge losses; flow and heat decoupled (viscosity independent of T; chip switches on after the force period).

## 5. Application model (initial condition)

- Click: dome of fixed volume (default 0.1 mL equivalent; user-adjustable in the app).
- Hold: extrusion at constant volume rate Q at the cursor.
- Drag: bead with volume per length = Q / cursor speed.
- Output: deposit thickness map s(x,y), shown live; then apply the pancake rule.

## 6. Numerical method

- Square grid N x N (start N = 100; test N = 50, 100, 200). Each cell stores a fill fraction phi.
- Per time step: solve laplacian(p_hat) = -12 mu / h^3 on wet cells (p_hat = 0 at faces adjacent to dry or partial cells and at the plate boundary, where paste exits). Then U = F/integral(p_hat dA), face fluxes q = -(h^3/12mu) dp/dn, advance h by -U dt, push flux into partial/dry cells until their volume h dx^2 is full, then mark them wet. Adaptive dt so no cell overfills in one step. Fluxes leaving through the plate boundary are accumulated as spilled volume and discarded.
- Mention and, if feasible, reduce the staircase/half-cell error of Dirichlet conditions on a grid front (for example sub-cell distance correction); report the convergence with N against the circular-blob analytic result.
- Stop the squeeze when h = h_min or when the force period ends.
- Thermal (after the force stops), steady, on the same grid, with G = 1/(r h) under paste and k_air/h elsewhere:
  - lid: k_l t_l laplacian(T_l) + q'' = G (T_l - T_s)
  - sink: k_s t_s laplacian(T_s) + G (T_l - T_s) = h_c (T_s - T_amb)
  - Defaults (my choices, flag them as such in the report): lid copper k = 400 W/m K, t = 3 mm; heatsink base aluminium k = 200 W/m K, t = 5 mm, h_c = 2000 W/m2 K; T_amb = 25 C; 100 W uniform over a central 20 mm x 20 mm chip footprint.
  - Plot both the lid temperature and the paste top-surface (sink) temperature, plus the conductance map. Report the lateral spreading length sqrt(k_l t_l r h) and total thermal resistance.
- Reuse one sparse Poisson-type solver for the pressure and temperature problems.

## 7. Validation gates (run each, report numbers, stop and tell me if a gate fails)

1. Disc analytic results at three gaps (200, 100, 50 um): pressure profile, force at fixed U, time at fixed F; plot F vs h on log-log (slope -3).
2. Numerical solver on a fully filled square vs the equal-area disc; quantify the difference.
3. Free-boundary blob: a circular start reproduces R = sqrt(Vol/(pi h)), force slope -5 then -3 at the plate edge; global volume balance (flux through boundary = U x wet area, plus spilled volume); similarity collapse of h/h0 vs t/tau for different mu and F.
4. Thermal: uniform paste gives dT = q'' r h exactly; energy balance (heat in = heat out to ambient) to a tight tolerance; limiting cases (paste everywhere vs a large dry patch).

## 8. Build stages

A: analytic module + plots (Tier 1 deliverable). B: 2D solver on the fully filled square. C: free-boundary blob with spills. D: interactive application (click / hold / drag, force on/off timing, live pressure and thickness maps). E: thermal solver and maps. Deliver and validate stage by stage; do not move on with a failed gate.

## 9. Deliverables

Code (modular, commented, one README with run instructions); validation plots and tables; a short assumptions-and-omissions list; a list of what the model omits (non-Newtonian shear thinning and yield stress, filler jamming and a real minimum bond-line thickness, viscosity vs temperature, surface tension/wetting, tilt, roughness, air entrapment, pump-out, contact resistance, edge losses, transient heating).

## 10. How to explain (strict)

Explain from structural foundations first, why the basis is built the way it is, not only how to use it. Define every symbol and new concept inline the first time it appears ("here X is a Y, which means..."). Use one consistent term per quantity; say explicitly when two different-looking things are the same mathematical structure. No circular explanations, no black boxes. Be direct: no praise or filler. If something in this brief is inconsistent or cannot be validated, say so plainly instead of padding. Remember the audience is 3rd-semester: explain, but do not skip steps.

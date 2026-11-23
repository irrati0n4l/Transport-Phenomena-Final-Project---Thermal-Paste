# Squeeze Flow of Non-Newtonian Thermal Interface Materials in 700 W AI GPU Packaging: First-Principles Transport Phenomena, Rheological Closure, and Coupled Bondline Thermal Resistance

**Transport Phenomena Final Project Report**  
Department of Materials Science and Metallurgical Engineering  
Course Instructor: Prof. Saswata Bhattacharyya  
November 2026

---

## Abstract

Modern artificial-intelligence accelerators such as 700 W H100-class GPUs reject heat fluxes exceeding $86\,\text{W/cm}^2$ across die areas of $A_{\text{die}} = 814\,\text{mm}^2$. The dominant thermal bottleneck between the silicon die and the cold plate is the Thermal Interface Material (TIM)—a dense particle-laden suspension dispensed as a constant-volume "pea-dot" ($V_0 = 50\,\text{mm}^3$) and compressed under a constant clamping load ($F_0 = 400\,\text{N}$). In this work, we synthesize the foundational principles of transport phenomena from the course lecture series—*Conservation and Transport Equations* (Deck 1), *Momentum, Energy and Fluid Flow* (Deck 2), and *Dimensionless Numbers as Ratios of Physical Effects* (Deck 3)—to derive, verify, and contrast the axisymmetric constant-volume and die-capped constant-area squeeze flow of three rheological classes: (i) Newtonian fluids (Stefan's law), (ii) Ostwald–de Waele power-law fluids (Scott's equation for shear-thinning $n<1$ and shear-thickening $n>1$ pastes), and (iii) Bingham yield-stress fluids (Covey–Stanmore lubrication theory and the Lipscomb–Denn pseudo-plug paradox). We derive closed-form and semi-analytical solutions for the local velocity profiles $u_r(r,z)$, universal linear shear-stress fields $\tau_{rz}(r,z)$, radial pressure distributions $p(r)$, and two-phase bondline trajectories $h(t)$ and $R(t)$. Coupling momentum transport to steady 1D Fourier conduction across a parallel TIM/air-gap resistance network reveals a critical hardware failure regime: while shear-thinning paste ($n=0.5$) achieves 100% die coverage and thins to $h(60\,\text{s}) = 10.77\,\mu\text{m}$ ($\Delta T_{\text{TIM}} = 1.85\,\text{K}$), a heavily loaded Bingham paste with high yield stress ($\tau_y = 5\,\text{kPa}$) permanently stalls in the plastic limit ($\Phi(\Lambda\to 0)=1$) at $h^* = 77.32\,\mu\text{m}$ and $R^* = 14.35\,\text{mm}$ ($79.4\%$ coverage), trapping an insulating peripheral air annulus ($k_{\text{air}} = 0.026\,\text{W/(m}\cdot\text{K)}$) that elevates the mean TIM temperature drop to $16.71\,\text{K}$ and induces a severe $2557\,\text{K}$ 1D perimeter hotspot penalty. All models are validated via a 20-check automated verification suite confirming limiting cases, volume/force conservation, ODE-vs.-closed-form agreement, Bingham-vs.-Newtonian thickness ordering, asymptotic scaling exponents, and dimensional homogeneity to machine precision.

---

## 1. Introduction and Physical Motivation

In high-performance semiconductor packaging, heat generated within the active silicon die must cross a thin polymer-matrix composite layer known as the Thermal Interface Material (TIM) before reaching the vapour chamber or liquid cold plate. Even optically polished silicon and copper surfaces make true solid–solid contact over less than $1\text{–}2\%$ of their nominal area; the remaining $98\%$ consists of microscopic air pockets whose thermal conductivity ($k_{\text{air}} = 0.026\,\text{W/(m}\cdot\text{K)}$) is nearly two hundred times lower than that of commercial particle-filled thermal pastes ($k_{\text{TIM}} \approx 5.0\,\text{W/(m}\cdot\text{K)}$).

During assembly, a fixed volume $V_0$ of paste is dispensed at the center of the die of area $A_{\text{die}}$ (modeled as an equivalent circular disk of radius $R_{\text{die}} = \sqrt{A_{\text{die}}/\pi}$) and compressed under a constant spring-loaded heatsink clamping force $F_0$. As the upper surface descends from an initial dot height $h_0$ to a time-dependent bondline thickness (BLT) $h(t)$ at squeeze rate $W(t) \equiv -\dot{h}(t) > 0$, the paste spreads radially outward to a wetted radius $R(t)$.

This single industrial process provides an ideal physical laboratory for the unifying philosophy of our Transport Phenomena course (Deck 2, Slide 184):

> *"Conservation is universal; closure is material specific. Mass conservation $+$ momentum conservation $+$ energy conservation apply to every material model. The stress law distinguishes Newtonian fluid, power-law fluid, yield-stress fluid, viscoelastic material. The same geometry can give different velocity and stress fields when rheology changes."*

Table 1 maps every physical and mathematical concept used in this report directly to the course slide decks and textbook chapters [2, 3, 8, 9]. Table 2 summarizes the 700 W AI GPU hardware benchmark parameters defined in `src/params.py`.

### Table 1: Synthesis of Transport Phenomena Course Concepts Applied to TIM Squeeze Flow

| Course Module | Lecture Slide & Welty Ref. | Specific Application in TIM Squeeze-Flow Model |
|---|---|---|
| Control Volumes (CV) vs. Material Systems | Deck 1, Slides 3–4, 8, 14–15; Deck 2, Slides 5–6, 11, 34; Welty Ch. 4 | Fixed-radius, shrinking-height deformable cylindrical pillbox CV $V(t)=\pi r^2 h(t)$ inside the spreading droplet. |
| Leibniz Rule & Moving Boundaries | Deck 1, Slides 16–18, 60–63 | Time differentiation of an integral over a domain with moving upper plate boundary $z=h(t)$ at speed $\vec{w}=\dot{h}\vec{e}_z$. |
| 3D Reynolds Transport Theorem (RTT) & Continuity | Deck 1, Slides 32–37; Deck 2, Slides 35, 80, 135; Welty Ch. 4 | Deriving the universal kinematic constraint $q_r(r) = \int_0^h u_r\,dz = r(-\dot{h})/2$ and constant-volume law $V_0 = \pi R(t)^2 h(t)$. |
| Cauchy Stress Tensor & Traction Vectors | Deck 2, Slides 3, 13–32, 56, 84; Welty Ch. 7 | Decomposition $\underline{\underline{\sigma}} = -p\underline{\underline{I}} + \underline{\underline{\tau}}$, outward normal tractions $\vec{t}^{(\vec{n})} = \underline{\underline{\sigma}}\vec{n}$, and normal compressive pressure convention $p > 0$. |
| Cauchy Momentum & Stress Divergence | Deck 2, Slides 76–85, 120–125, 133–136 | Axisymmetric cylindrical momentum balance $\rho D\vec{u}/Dt = -\nabla p + \nabla\cdot\underline{\underline{\tau}}$ before constitutive closure; every term has units $\text{N/m}^3$. |
| Deformation-Rate Tensor & Simple Shear | Deck 2, Slides 86–92, 188–190 | Velocity gradient $\underline{\underline{G}}=\nabla\vec{u}$, symmetric strain-rate $\underline{\underline{D}}=\frac{1}{2}(\underline{\underline{G}}+\underline{\underline{G}}^T)$, and thin-gap dominant shear rate $\dot{\gamma} = \partial u_r/\partial z$. |
| Non-Newtonian Rheology (Power-Law & Bingham) | Deck 2, Slides 94–98, 184–185; Welty Ch. 7 | Material-specific closure: Newtonian ($\tau=\mu\dot{\gamma}$), Power-Law ($\tau=K\lvert\dot{\gamma}\rvert^{n-1}\dot{\gamma}$), and Bingham plastic ($\tau=\tau_y\,\text{sgn}(\dot{\gamma})+\mu_p\dot{\gamma}$). |
| Lubrication Reduction & Parallel Slit Flow | Deck 2, Slides 99–107, 145–146, 153–157; Welty Ch. 8 | Term-by-term deletion via $\epsilon = h/R \ll 1$ and $Re_{\text{sq}} \ll 1$, reducing $r$-momentum to local Poiseuille-like slit flow $0 = -\partial p/\partial r + \partial\tau_{rz}/\partial z$. |
| Units, Force Scales & Buckingham $\Pi$ Theorem | Deck 3, Slides 3–8, 13–16, 31–32, 50–53; Welty Ch. 11 | Base dimensions $[M,L,T]$, dimensional matrix rank $r=3$, $n-r$ $\Pi$-groups ($\epsilon$, $Re_{\text{sq}}$, $Bn$, $n$, $\Phi(\Lambda)$), and assumption-validity tracking. |
| Fourier's Law & Boundary Thermal Resistance | Deck 1, Slides 48–50; Deck 3, Slides 23–26, 52; Welty Ch. 15 | Steady 1D conduction $\vec{q}=-k\nabla T$ across the bondline and parallel thermal-resistance network ($R_{\text{cov}} \parallel R_{\text{air}}$) for partial die coverage. |
| 7-Point Verification Checklist | Deck 1, Slide 83 | Automated 20-check suite verifying CV definition, flux signs, limiting cases ($n\to 1$, $\tau_y\to 0$, $W\to 0$), ODE vs. closed-form consistency, Bingham thickness ordering, conservation, and unit invariance. |

### Table 2: 700 W AI GPU Benchmark & Material Specifications (`src/params.py`)

| Quantity | Symbol | Benchmark Value [SI Units] |
|---|---|---|
| Die area | $A_{\text{die}}$ | $814\,\text{mm}^2 = 8.14\times 10^{-4}\,\text{m}^2$ |
| Equivalent die radius | $R_{\text{die}}$ | $\sqrt{A_{\text{die}}/\pi} = 16.10\,\text{mm}$ |
| Thermal design power | $\dot{Q}$ | $700\,\text{W}$ ($q'' = 86.0\,\text{W/cm}^2$) |
| Clamping load | $F_0$ | $400\,\text{N}$ (constant force) |
| Dispensed volume | $V_0$ | $50\,\text{mm}^3 = 5.0\times 10^{-8}\,\text{m}^3$ |
| Initial dot height | $h_0$ | $1.00\,\text{mm}$ ($R_0 = 3.99\,\text{mm}$) |
| Cap thickness | $h_c$ | $V_0/A_{\text{die}} = 61.43\,\mu\text{m}$ |
| Mount hold time | $t_{\text{mount}}$ | $60.0\,\text{s}$ |
| Paste density | $\rho$ | $2500\,\text{kg/m}^3$ |
| Newtonian viscosity | $\mu$ | $100\,\text{Pa}\cdot\text{s}$ |
| Power-law consistency | $K$ | $100\,\text{Pa}\cdot\text{s}^n$ ($n \in \{0.5, 1.3\}$) |
| Bingham parameters | $\mu_p, \tau_y$ | $100\,\text{Pa}\cdot\text{s}$, $\tau_y \in \{250, 5000\}\,\text{Pa}$ |
| Conductivities | $k_{\text{TIM}}, k_{\text{air}}$ | $5.0$, $0.026\,\text{W/(m}\cdot\text{K)}$ |

---

## 2. Deformable Control Volume and Continuity via Reynolds Transport Theorem

### 2.1 Material System vs. Deformable Control Volume

Following Deck 1 (Slides 3–4, 32–34) and Deck 2 (Slides 5–6, 11, 34–35), we distinguish between the *material system* $M(t)$—which encloses the entire dispensed paste volume $V_0$ and deforms with the advancing contact line $R(t)$ so that zero mass crosses its boundary—and an internal *deformable control volume* $V(t)$ chosen to measure the radial velocity field $u_r(r,z,t)$ at any interior radius $r \le R(t)$.

We select $V(t)$ to be a coaxial cylinder of *fixed* radial coordinate $r$ and *time-varying* height $h(t)$ spanning $0 \le z \le h(t)$, bounded by the closed control surface $\partial V(t) = \mathcal{S}_{\text{bot}} \cup \mathcal{S}_{\text{top}}(t) \cup \mathcal{S}_{\text{side}}(t)$:

1. **Bottom die surface $\mathcal{S}_{\text{bot}}$ ($z = 0$, outward unit normal $\vec{n} = -\vec{e}_z$):** Stationary, impermeable solid wall. Both the fluid velocity $\vec{u}(r,0,t) = \vec{0}$ and control-surface velocity $\vec{w} = \vec{0}$ vanish, so $(\vec{u}-\vec{w})\cdot\vec{n} = 0$.
2. **Top cold-plate surface $\mathcal{S}_{\text{top}}(t)$ ($z = h(t)$, outward unit normal $\vec{n} = +\vec{e}_z$):** Impermeable solid wall descending at speed $\dot{h} = dh/dt < 0$. The control surface moves with the plate ($\vec{w} = \dot{h}\vec{e}_z$), and no-penetration/no-slip requires $\vec{u}(r,h,t) = \dot{h}\vec{e}_z$. Hence the relative crossing velocity is identically zero:

$$(\vec{u} - \vec{w})\cdot\vec{n}\big|_{z=h(t)} = (\dot{h} - \dot{h}) = 0. \tag{1}$$

Fluid never crosses the top boundary; instead, the downward motion of $\mathcal{S}_{\text{top}}(t)$ shrinks the volume of $V(t) = \pi r^2 h(t)$ (Deck 1, Slide 61).

3. **Lateral cylindrical surface $\mathcal{S}_{\text{side}}(t)$ (fixed radius $r$, $0 \le z \le h(t)$, outward normal $\vec{n} = +\vec{e}_r$):** Because $r$ is held fixed, the radial boundary velocity is zero ($\vec{w} = \vec{0}$). Thus the relative efflux velocity normal to $\mathcal{S}_{\text{side}}(t)$ is simply the radial fluid velocity:

$$(\vec{u} - \vec{w})\cdot\vec{n}\big|_{\mathcal{S}_{\text{side}}} = \vec{u}\cdot\vec{e}_r = u_r(r,z,t). \tag{2}$$

### 2.2 Integral RTT Derivation of the Radial Flux Constraint

For a general intensive quantity per unit volume ($C = \rho$ for total mass), the 3D Reynolds Transport Theorem for a control volume with moving boundary velocity $\vec{w}$ (Deck 1, Slide 36; Deck 2, Slide 35) connects the material derivative of the system $M(t)$ instantaneously coinciding with $V(t)$ to control-volume integrals:

$$\frac{d}{dt}\int_{M(t)} \rho\,dV = \frac{d}{dt}\int_{V(t)} \rho\,dV + \oint_{\partial V(t)} \rho(\vec{u} - \vec{w})\cdot\vec{n}\,dA = 0. \tag{3}$$

Because the highly filled silicone paste is incompressible ($\rho = \text{const}$), $\rho$ factors out of both integrals:

$$\frac{d}{dt}\underbrace{\left(\int_{V(t)} dV\right)}_{\pi r^2 h(t)} + \int_{\mathcal{S}_{\text{side}}(t)} u_r(r,z,t)\,dA = 0. \tag{4}$$

On the cylindrical side wall of fixed radius $r$, an infinitesimal ring of height $dz$ has differential area $dA = 2\pi r\,dz$. Evaluating the time derivative of the pillbox volume at fixed $r$ yields:

$$\pi r^2 \frac{dh}{dt} + 2\pi r \int_0^{h(t)} u_r(r,z,t)\,dz = 0. \tag{5}$$

Defining the positive downward squeeze rate $W(t) \equiv -\dot{h}(t) = -dh/dt > 0$ and the radial volumetric flow rate per unit circumference $q_r(r,t) \equiv \int_0^{h(t)} u_r(r,z,t)\,dz$ (with SI units $[\text{m}^2/\text{s}]$), we obtain the fundamental kinematic identity valid for *all* rheological models:

$$\boxed{q_r(r,t) \equiv \int_0^{h(t)} u_r(r,z,t)\,dz = -\frac{r\dot{h}(t)}{2} = \frac{r\,W(t)}{2}.} \tag{6}$$

Equation (6) has a direct physical interpretation (Deck 1, Slides 14–15): the volume of paste displaced per unit time inside radius $r$ scales with the disk area $\pi r^2 W$, whereas the exit perimeter scales only with the circumference $2\pi r$. Their ratio $(\pi r^2 W)/(2\pi r) = rW/2$ forces the depth-averaged radial speed $\bar{u}_r(r) = q_r/h = rW/(2h)$ to grow linearly from zero at the stagnation axis ($r=0$) to its maximum at the outer rim ($r=R$).

### 2.3 Equivalence with Differential Continuity and Two-Phase Wetted Radius

Applying Gauss's divergence theorem (Deck 1, Slides 25–30; Deck 2, Slide 80) to a fixed infinitesimal volume gives the local continuity equation $\partial\rho/\partial t + \nabla\cdot(\rho\vec{u}) = 0$, which for constant density reduces to $\nabla\cdot\vec{u} = 0$. In axisymmetric cylindrical coordinates $(r,\theta,z)$ with $u_\theta = 0$ and $\partial/\partial\theta = 0$:

$$\frac{1}{r}\frac{\partial(r u_r)}{\partial r} + \frac{\partial u_z}{\partial z} = 0. \tag{7}$$

Integrating Eq. (7) vertically from $z=0$ to $z=h(t)$ and pulling $\frac{1}{r}\frac{\partial}{\partial r}$ outside the $z$-integral (since $h(t)$ is independent of $r$ for parallel plates; Deck 1, Slide 16) gives:

$$\frac{1}{r}\frac{\partial}{\partial r}\left(r\int_0^{h(t)} u_r\,dz\right) + \Bigl[u_z(r,h,t) - u_z(r,0,t)\Bigr] = 0. \tag{8}$$

Substituting $u_z(r,0,t)=0$ and $u_z(r,h,t)=\dot{h}=-W$ yields $\frac{1}{r}\frac{\partial(r q_r)}{\partial r} = W$. Integrating with respect to $r$ and imposing finiteness at $r=0$ ($q_r(0)=0$) recovers Eq. (6) identically.

Applying mass conservation to the entire dispensed droplet of volume $V_0 = \pi R_0^2 h_0$ defines two sequential geometric phases during clamping:

1. **Phase 1 — Constant-Volume Radial Spreading ($h_c < h(t) \le h_0$):** The paste footprint lies entirely inside the die perimeter ($R(t) < R_{\text{die}}$), so total paste volume is conserved:

$$\pi R(t)^2 h(t) = V_0 \implies R(t) = \sqrt{\frac{V_0}{\pi h(t)}}. \tag{9}$$

2. **Phase 2 — Die-Capped Constant-Area Squeeze ($h(t) \le h_c$):** Once the paste reaches the die edge $R(t) = R_{\text{die}}$ at the critical cap thickness

$$h_c = \frac{V_0}{\pi R_{\text{die}}^2} = \frac{V_0}{A_{\text{die}}} = 61.43\,\mu\text{m}, \tag{10}$$

the active load-bearing contact radius remains pinned at $R(t) = R_{\text{die}}$ while excess paste overflows past the die perimeter where $p(R_{\text{die}}) = p_\infty$.

Combining both phases gives the unified wetted radius law implemented in `src/rheology_models.py`:

$$\boxed{R(h) = \min\!\left(\sqrt{\frac{V_0}{\pi h}},\, R_{\text{die}}\right).} \tag{11}$$

---

## 3. Cauchy Momentum Balance and Thin-Gap Lubrication Reduction

### 3.1 Stress Tensor Decomposition and Cylindrical Cauchy Equations

Following Deck 2 (Slides 13–32, 76–85), the surface traction vector $\vec{t}^{(\vec{n})}$ acting on an arbitrary surface element with outward normal $\vec{n}$ is given by Cauchy's relation $\vec{t}^{(\vec{n})} = \underline{\underline{\sigma}}\vec{n}$. Because positive normal stress denotes tension whereas thermodynamic pressure $p > 0$ is compressive (Deck 2, Slides 29–32), the total Cauchy stress tensor $\underline{\underline{\sigma}}$ decomposes into an isotropic pressure tensor $-p\underline{\underline{I}}$ and a deformation-driven extra (deviatoric) stress tensor $\underline{\underline{\tau}}$:

$$\underline{\underline{\sigma}} = -p\underline{\underline{I}} + \underline{\underline{\tau}} \implies \nabla\cdot\underline{\underline{\sigma}} = -\nabla p + \nabla\cdot\underline{\underline{\tau}}. \tag{12}$$

Substituting this into the local momentum balance (Deck 2, Slides 79–85) yields the Cauchy momentum equation prior to selecting any rheology:

$$\rho\frac{D\vec{u}}{Dt} = \rho\left(\frac{\partial\vec{u}}{\partial t} + (\vec{u}\cdot\nabla)\vec{u}\right) = -\nabla p + \nabla\cdot\underline{\underline{\tau}} + \rho\vec{b}. \tag{13}$$

Every term in Eq. (13) represents a force per unit volume with SI units $\text{N/m}^3 = \text{kg/(m}^2\cdot\text{s}^2)$ (Deck 2, Slide 136). In axisymmetric cylindrical coordinates $(r,\theta,z)$ with $u_\theta = 0$, $\partial/\partial\theta = 0$, and negligible gravitational body force compared to the clamping pressure ($\rho g h \sim 1\,\text{Pa} \ll F_0/A_{\text{die}} \approx 5\times 10^5\,\text{Pa}$), the radial ($r$) and axial ($z$) components of Eq. (13) are:

$$\begin{aligned}
\rho\left(\frac{\partial u_r}{\partial t} + u_r\frac{\partial u_r}{\partial r} + u_z\frac{\partial u_r}{\partial z}\right) &= -\frac{\partial p}{\partial r} + \frac{1}{r}\frac{\partial(r\tau_{rr})}{\partial r} - \frac{\tau_{\theta\theta}}{r} + \frac{\partial\tau_{rz}}{\partial z}, \\
\rho\left(\frac{\partial u_z}{\partial t} + u_r\frac{\partial u_z}{\partial r} + u_z\frac{\partial u_z}{\partial z}\right) &= -\frac{\partial p}{\partial z} + \frac{1}{r}\frac{\partial(r\tau_{rz})}{\partial r} + \frac{\partial\tau_{zz}}{\partial z}.
\end{aligned} \tag{14–15}$$

### 3.2 Scale Analysis and Lubrication Reduction

Following the systematic reduction rules in Deck 2 (Slides 143–146) and Deck 3 (Slides 7–8, 16), each deleted term requires an explicit physical and scaling justification based on the geometric aspect ratio $\epsilon$:

$$\epsilon(t) \equiv \frac{h(t)}{R(t)} \ll 1. \tag{16}$$

For our 700 W GPU benchmark, even at the initial moment $t=0$ ($h_0 = 1\,\text{mm}$, $R_0 = 3.99\,\text{mm}$), $\epsilon$ rapidly drops below $10^{-2}$ within the first second and reaches $\epsilon \sim 10^{-3}$ at operational bondlines ($h \sim 15\text{–}60\,\mu\text{m}$, $R \sim 16.1\,\text{mm}$). Introducing characteristic scales

$$r \sim R, \quad z \sim h = \epsilon R, \quad u_z \sim W, \quad u_r \sim U_r = \frac{RW}{h} = \frac{W}{\epsilon}, \quad t \sim \frac{h}{W}, \tag{17}$$

we compare the components of the velocity-gradient tensor $\underline{\underline{G}} = \nabla\vec{u}$ and symmetric deformation-rate tensor $\underline{\underline{D}} = \frac{1}{2}(\underline{\underline{G}}+\underline{\underline{G}}^T)$ (Deck 2, Slides 87–89):

$$\begin{aligned}
\frac{\partial u_r}{\partial z} &\sim \frac{U_r}{h} = \frac{RW}{h^2} = \frac{W}{\epsilon^2 R}, &
\frac{\partial u_z}{\partial r} &\sim \frac{W}{R} = \epsilon^2 \left(\frac{\partial u_r}{\partial z}\right), \\
\frac{\partial u_r}{\partial r},\; \frac{u_r}{r},\; \frac{\partial u_z}{\partial z} &\sim \frac{U_r}{R} = \frac{W}{h} = \epsilon \left(\frac{\partial u_r}{\partial z}\right).
\end{aligned} \tag{18–19}$$

Consequently, the engineering shear rate $\dot{\gamma} \equiv 2D_{rz} = \frac{\partial u_r}{\partial z} + \frac{\partial u_z}{\partial r}$ is completely dominated by the vertical gradient of radial velocity:

$$\dot{\gamma} = \frac{\partial u_r}{\partial z}\Bigl[1 + \mathcal{O}(\epsilon^2)\Bigr] \simeq \frac{\partial u_r}{\partial z}. \tag{20}$$

In the radial momentum balance (14), the transverse shear-stress derivative scales as $\partial\tau_{rz}/\partial z \sim \tau_c/h$, whereas the in-plane normal-stress derivatives scale as $\frac{1}{r}\partial(r\tau_{rr})/\partial r \sim \epsilon(\tau_c/R) = \epsilon^2(\partial\tau_{rz}/\partial z)$. Dropping $\mathcal{O}(\epsilon^2)$ terms eliminates $\tau_{rr}$ and $\tau_{\theta\theta}$.

Next, comparing the convective inertia scale $\rho u_r \partial u_r/\partial r \sim \rho U_r^2 / R$ against the dominant viscous force scale $\partial\tau_{rz}/\partial z \sim \mu_{\text{eff}} U_r / h^2$ defines the **Squeeze Reynolds Number** $Re_{\text{sq}}$ (Deck 2, Slides 143–145; Deck 3, Slide 8):

$$\frac{\text{inertial force scale}}{\text{viscous force scale}} \sim \frac{\rho U_r^2 / R}{\mu_{\text{eff}} U_r / h^2} = \frac{\rho U_r h^2}{\mu_{\text{eff}} R} = \boxed{\frac{\rho W h}{\mu_{\text{eff}}} \equiv Re_{\text{sq}}.} \tag{21}$$

With $\rho = 2500\,\text{kg/m}^3$, $h \sim 5\times 10^{-5}\,\text{m}$, $W \sim 10^{-5}\,\text{m/s}$, and $\mu_{\text{eff}} \sim 100\,\text{Pa}\cdot\text{s}$, we find $Re_{\text{sq}} \sim 10^{-11} \ll 1$, placing the entire squeeze trajectory deep inside the creeping (Stokes) flow regime.

Finally, in the axial momentum balance (15), $\partial p/\partial z \sim \frac{1}{r}\partial(r\tau_{rz})/\partial r \sim \tau_c/R$, whereas in the radial equation $\partial p/\partial r \sim \tau_c/h$. Thus the axial pressure variation $\Delta p_z \sim h(\partial p/\partial z) \sim \epsilon^2 \Delta p_r$ is negligible to $\mathcal{O}(\epsilon^2)$. The governing lubrication equations therefore reduce to:

$$\boxed{\frac{\partial p}{\partial z} = 0 \implies p = p(r,t), \qquad 0 = -\frac{\partial p}{\partial r} + \frac{\partial\tau_{rz}}{\partial z}.} \tag{22}$$

### 3.3 Universal Linear Shear-Stress Distribution Across the Gap

Because $p = p(r,t)$ is independent of $z$, we define the local radial pressure gradient $G(r,t) \equiv -\frac{\partial p}{\partial r}(r,t) > 0$ (positive since pressure peaks at $r=0$ and decays to $p_\infty$ at $r=R$, driving outward flow in $+r$; Deck 2, Slide 154). Integrating Eq. (22) with respect to $z$ gives $\tau_{rz}(r,z) = -G(r)z + C_1(r)$.

By reflection symmetry about the midplane $z = h/2$ (both plates at $z=0$ and $z=h$ enforce the no-slip radial boundary condition $u_r(r,0) = u_r(r,h) = 0$; Deck 2, Slides 137, 146), the radial velocity profile is symmetric across the gap and attains its maximum at $z = h/2$, where the shear stress vanishes: $\tau_{rz}(r,h/2) = 0$. Defining the midplane-centered vertical coordinate

$$\zeta \equiv z - \frac{h}{2} \in \bigl[-H, +H\bigr], \qquad H \equiv \frac{h}{2}, \tag{23}$$

gives the **universal linear shear-stress distribution**:

$$\boxed{\tau_{rz}(r,z) = -G(r)\left(z - \frac{h}{2}\right) = -G(r)\,\zeta.} \tag{24}$$

Crucially, Eq. (24) follows purely from momentum conservation and midplane symmetry *before* introducing any constitutive stress–strain-rate relation. At the lower die wall ($z=0, \zeta=-H$), $\tau_{rz}(r,0) = +G(r)H > 0$; at the upper plate ($z=h, \zeta=+H$), $\tau_{rz}(r,h) = -G(r)H < 0$, exerting inward drag opposing the outward radial pressure force (Deck 2, Slides 105–107, 153).

---

## 4. Constitutive Closure and Analytical Squeeze-Flow Solutions

With conservation equations (6) and (24) established, we now close the model for each of the three candidate TIM rheologies following the flowchart on Slide 185 of Deck 2.

### 4.1 Model 1: Newtonian Fluid (Stefan's Law)

For a Newtonian paste of constant dynamic viscosity $\mu$ (Deck 2, Slides 91–92), the shear stress in simple thin-gap shear is:

$$\tau_{rz} = \mu\frac{\partial u_r}{\partial z} = \mu\frac{\partial u_r}{\partial\zeta} = -G(r)\,\zeta. \tag{25}$$

Integrating with respect to $\zeta$ and applying the no-slip condition $u_r(\zeta = \pm H) = 0$ yields the locally parabolic Poiseuille velocity profile (Deck 2, Slides 154–156):

$$\boxed{u_r(r,z) = \frac{G(r)}{2\mu}\left(H^2 - \zeta^2\right) = \frac{G(r)}{2\mu}z(h-z).} \tag{26}$$

Integrating Eq. (26) across the gap thickness gives the volumetric flux per unit circumference:

$$q_r(r) = 2\int_0^H \frac{G(r)}{2\mu}(H^2 - \zeta^2)\,d\zeta = \frac{2G(r)H^3}{3\mu} = \frac{G(r)h^3}{12\mu}. \tag{27}$$

Equating this flux with the RTT continuity constraint (6), $q_r(r) = rW/2$, determines the radial pressure gradient:

$$-\frac{\partial p}{\partial r} = G(r) = \frac{6\mu W r}{h^3}. \tag{28}$$

Integrating Eq. (28) from $r$ to the free paste boundary $R$ where gauge pressure vanishes ($p(R) = p_\infty$, Deck 2, Slide 41) gives the parabolic radial pressure distribution:

$$\boxed{p(r) - p_\infty = \frac{3\mu W}{h^3}\left(R^2 - r^2\right).} \tag{29}$$

Integrating the gauge pressure over the wetted disk area yields Stefan's squeeze-force law [4]:

$$F = \int_0^R \bigl(p(r) - p_\infty\bigr)\,2\pi r\,dr = \frac{3\pi\mu W}{h^3}\left[\frac{R^2 r^2}{2} - \frac{r^4}{4}\right]_0^R = \boxed{\frac{3\pi\mu W R^4}{2h^3}.} \tag{30}$$

Under constant clamping force $F = F_0$ with $W = -dh/dt$:

* **Phase 1 (Constant Volume, $R^2 = V_0/(\pi h)$, $h > h_c$):** Substituting $R^4 = V_0^2/(\pi^2 h^2)$ into Eq. (30) strengthens the gap dependence from $h^{-3}$ to $h^{-5}$:

$$F_0 = \frac{3\mu V_0^2}{2\pi h^5}\left(-\frac{dh}{dt}\right) \implies -h^{-5}\,dh = \frac{2\pi F_0}{3\mu V_0^2}\,dt. \tag{31}$$

Integrating from $(t=0, h=h_0)$ yields the exact Phase 1 trajectory:

$$\boxed{h(t) = h_0\left(1 + \frac{8\pi F_0 h_0^4}{3\mu V_0^2}\,t\right)^{-1/4}} \implies h(t) \propto t^{-1/4}, \;\; R(t) \propto t^{1/8}. \tag{32}$$

* **Phase 2 (Die-Capped Constant Area, $R = R_{\text{die}}$, $t \ge t_c$):** The dot reaches $R_{\text{die}}$ ($h = h_c$) at transition time

$$t_c = \frac{3\mu V_0^2}{8\pi F_0 h_0^4}\left[\left(\frac{h_0}{h_c}\right)^4 - 1\right]. \tag{33}$$

For $t \ge t_c$, $R = R_{\text{die}}$ is constant in Eq. (30), so $-h^{-3}\,dh = \frac{2F_0}{3\pi\mu R_{\text{die}}^4}\,dt$, giving:

$$\boxed{h(t) = \left[h_c^{-2} + \frac{4F_0(t - t_c)}{3\pi\mu R_{\text{die}}^4}\right]^{-1/2}} \implies h(t) \propto t^{-1/2}. \tag{34}$$

### 4.2 Model 2: Ostwald–de Waele Power-Law Fluid (Scott's Law)

For a power-law paste with consistency index $K$ ($\text{Pa}\cdot\text{s}^n$) and flow-behavior index $n$ (Deck 2, Slide 95), the shear stress is $\tau_{rz} = K|\dot{\gamma}|^{n-1}\dot{\gamma}$. In the upper half of the gap $\zeta \in [0, H]$, velocity decreases toward the wall ($\partial u_r/\partial\zeta \le 0$) and $\tau_{rz} = -G\zeta \le 0$, so:

$$K\left(-\frac{\partial u_r}{\partial\zeta}\right)^n = G(r)\,\zeta \implies -\frac{\partial u_r}{\partial\zeta} = \left(\frac{G(r)}{K}\right)^{1/n}\zeta^{1/n}. \tag{35}$$

Integrating from $\zeta$ to $H$ with no-slip $u_r(\pm H) = 0$ ($H = h/2$) yields the power-law radial velocity profile:

$$\boxed{u_r(r,z) = \frac{n}{n+1}\left(\frac{G(r)}{K}\right)^{1/n}\left(H^{\frac{n+1}{n}} - |\zeta|^{\frac{n+1}{n}}\right).} \tag{36}$$

For shear-thinning pastes ($n < 1$), the exponent $(n+1)/n > 2$ flattens the core and sharpens the near-wall velocity gradient; for shear-thickening pastes ($n > 1$), $(n+1)/n < 2$ makes the profile more pointed than a parabola. Integrating Eq. (36) across $\zeta \in [-H, H]$ gives the radial volumetric flux:

$$\begin{aligned}
q_r(r) &= \frac{2n}{n+1}\left(\frac{G}{K}\right)^{1/n}\left[H^{\frac{n+1}{n}}\zeta - \frac{n}{2n+1}\zeta^{\frac{2n+1}{n}}\right]_0^H \\
&= \frac{2n}{2n+1}\left(\frac{G(r)}{K}\right)^{1/n} H^{\frac{2n+1}{n}} = \frac{n}{2n+1}\left(\frac{G(r)}{K}\right)^{1/n}\left(\frac{h}{2}\right)^{\frac{2n+1}{n}}.
\end{aligned} \tag{37}$$

Equating $q_r(r)$ with the RTT flux $rW/2$ from Eq. (6) and solving for $G(r)$ gives:

$$\boxed{G(r) = -\frac{\partial p}{\partial r} = \frac{2K}{h^{2n+1}}\left(\frac{2n+1}{n}\right)^n W^n r^n.} \tag{38}$$

Integrating Eq. (38) from $r$ to $R$ with $p(R) = p_\infty$ yields the power-law pressure distribution:

$$\boxed{p(r) - p_\infty = \frac{2K}{(n+1)h^{2n+1}}\left(\frac{2n+1}{n}\right)^n W^n\left(R^{n+1} - r^{n+1}\right).} \tag{39}$$

Integrating $p(r)-p_\infty$ over the disk area ($\int_0^R (R^{n+1}-r^{n+1})2\pi r\,dr = \pi R^{n+3}\frac{n+1}{n+3}$) yields Scott's squeeze-force equation [5]:

$$\boxed{F = \frac{2\pi K}{n+3}\left(\frac{2n+1}{n}\right)^n \frac{W^n R^{n+3}}{h^{2n+1}}.} \tag{40}$$

*Limiting-Case Check ($n = 1, K = \mu$):* Substituting $n=1$ into Eq. (40) gives $F = \frac{2\pi\mu}{4}(3)^1\frac{WR^4}{h^3} = \frac{3\pi\mu W R^4}{2h^3}$, recovering Stefan's Newtonian equation (30) identically.

For constant clamping force $F = F_0$:

* **Phase 1 (Constant Volume, $R = \sqrt{V_0/(\pi h)}$, $h > h_c$):** Substituting $R^{n+3} = (V_0/\pi)^{(n+3)/2} h^{-(n+3)/2}$ into Eq. (40) gives:

$$F_0 = \frac{2\pi K}{n+3}\left(\frac{2n+1}{n}\right)^n \left(\frac{V_0}{\pi}\right)^{\frac{n+3}{2}}\frac{(-\dot{h})^n}{h^{\frac{5n+5}{2}}}. \tag{41}$$

Solving for $W = -dh/dt$ yields a separable power-law ODE:

$$-\frac{dh}{dt} = A\,h^m, \qquad m = \frac{5n+5}{2n}, \qquad A = \left[\frac{F_0(n+3)}{2\pi K\left(\frac{2n+1}{n}\right)^n}\right]^{1/n}\left(\frac{\pi}{V_0}\right)^{\frac{n+3}{2n}}. \tag{42}$$

Since $m > 1$ for all $n > 0$, integrating $\int_{h_0}^h (h')^{-m}\,dh' = -At$ gives the closed-form Phase 1 trajectory:

$$\boxed{h(t) = \Bigl[h_0^{1-m} + (m - 1)A\,t\Bigr]^{\frac{1}{1-m}}, \qquad \frac{1}{1-m} = -\frac{2n}{3n+5}.} \tag{43}$$

Thus the constitutive flow index $n$ directly alters the late-time power-law thinning exponent $h(t) \propto t^{-\frac{2n}{3n+5}}$:

$$n = 0.5 \implies h \propto t^{-2/13} = t^{-0.15385}, \qquad n = 1.0 \implies h \propto t^{-1/4} = t^{-0.25000}, \qquad n = 1.3 \implies h \propto t^{-2.6/8.9} = t^{-0.29213}. \tag{44}$$

* **Phase 2 (Die-Capped Constant Area, $R = R_{\text{die}}$, $t \ge t_c$):** Once $h$ reaches $h_c$ at $t_c = (h_c^{1-m} - h_0^{1-m})/[(m-1)A]$, holding $R = R_{\text{die}}$ fixed in Eq. (40) gives $-dh/dt = B\,h^k$ with $k = (2n+1)/n$ and $B = \bigl[F_0(n+3)/\bigl(2\pi K(\frac{2n+1}{n})^n R_{\text{die}}^{n+3}\bigr)\bigr]^{1/n}$:

$$\boxed{h(t) = \Bigl[h_c^{1-k} + (k - 1)B\,(t - t_c)\Bigr]^{\frac{1}{1-k}}, \qquad \frac{1}{1-k} = -\frac{n}{n+1}.} \tag{45}$$

### 4.3 Model 3: Bingham Yield-Stress Fluid (Covey–Stanmore Lubrication & Plastic Stall)

High-volume-fraction metallic or ceramic pastes behave as Bingham plastics with yield stress $\tau_y$ and plastic viscosity $\mu_p$ (Deck 2, Slide 96):

$$\begin{cases}
\tau_{rz} = \tau_y\,\text{sgn}(\dot{\gamma}) + \mu_p\dot{\gamma}, & \text{when } |\tau_{rz}| > \tau_y, \\
\dot{\gamma} = \dfrac{\partial u_r}{\partial z} = 0, & \text{when } |\tau_{rz}| \le \tau_y.
\end{cases} \tag{46}$$

From our universal linear shear-stress law (24), $|\tau_{rz}(r,\zeta)| = G(r)|\zeta|$ increases linearly from zero at the midplane $\zeta=0$ to $G(r)H$ at the walls $\zeta=\pm H$. Therefore, whenever $G(r)H > \tau_y$, the gap splits into an unyielded central core $|\zeta| \le z_0(r)$ and two sheared wall layers $z_0(r) < |\zeta| \le H$, where the half-plug thickness $z_0(r)$ and dimensionless plug fraction $\xi_0(r)$ are:

$$\boxed{z_0(r) = \frac{\tau_y}{G(r)}, \qquad \xi_0(r) \equiv \frac{z_0(r)}{H} = \frac{2\tau_y}{h\,G(r)} \in (0, 1].} \tag{47}$$

#### Step 1 — Piecewise Velocity Profile
In the upper yielded layer $\zeta \in [z_0, H]$, $\tau_{rz} = -G\zeta < -\tau_y$ and $\dot{\gamma} = \partial u_r/\partial\zeta < 0$, so Eq. (46) reads:

$$-\mu_p\frac{\partial u_r}{\partial\zeta} = G(r)\,\zeta - \tau_y. \tag{48}$$

Integrating from $\zeta$ to $H$ with no-slip $u_r(H) = 0$ and enforcing continuity at $\zeta = z_0$ gives:

$$\boxed{u_r(r,z) = \begin{cases}
\dfrac{G(r)}{2\mu_p}\left(H^2 - \zeta^2\right) - \dfrac{\tau_y}{\mu_p}(H - |\zeta|), & z_0(r) \le |\zeta| \le H, \\[8pt]
u_{\text{plug}}(r) = \dfrac{G(r)}{2\mu_p}\bigl(H - z_0(r)\bigr)^2 = \dfrac{G(r)h^2}{8\mu_p}\bigl(1 - \xi_0(r)\bigr)^2, & 0 \le |\zeta| < z_0(r).
\end{cases}} \tag{49}$$

#### Step 2 — Buckingham–Reiner Radial Flux & Normalised Cubic Equation
Integrating Eq. (49) across the gap thickness (easily evaluated by integration by parts, $q_r = 2\int_0^H u_r\,d\zeta = 2\int_{z_0}^H \zeta(-\frac{\partial u_r}{\partial\zeta})\,d\zeta = \frac{2G}{\mu_p}\int_{z_0}^H \zeta(\zeta - z_0)\,d\zeta$) gives the Buckingham–Reiner slot flux:

$$q_r(r) = \frac{2G(r)}{\mu_p}\left[\frac{H^3 - z_0^3}{3} - z_0\frac{H^2 - z_0^2}{2}\right] = \frac{G(r)h^3}{12\mu_p}\left(1 - \frac{3}{2}\xi_0 + \frac{1}{2}\xi_0^3\right). \tag{50}$$

Equating Eq. (50) with the RTT continuity flux $q_r(r) = rW/2$ from Eq. (6) and eliminating $G(r) = 2\tau_y/(h\xi_0)$ via Eq. (47) yields:

$$\frac{\tau_y h^2}{6\mu_p\,\xi_0}\left(1 - \frac{3}{2}\xi_0 + \frac{1}{2}\xi_0^3\right) = \frac{rW}{2}. \tag{51}$$

Defining the dimensionless local radial shear-rate parameter $S(r)$ and global rim parameter $\Lambda$:

$$\boxed{S(r) \equiv \frac{3\mu_p r W}{\tau_y h^2} = \Lambda\,\frac{r}{R}, \qquad \Lambda \equiv S(R) = \frac{3\mu_p R W}{\tau_y h^2} = \frac{3}{Bn},} \tag{52}$$

where $Bn \equiv \frac{\tau_y h^2}{\mu_p R W}$ is the squeeze **Bingham Number**, produces the exact normalised cubic equation for $\xi_0(r) \in (0, 1]$ [6]:

$$\boxed{\xi_0^3 - \bigl(3 + 2S(r)\bigr)\xi_0 + 2 = \bigl(1 - \xi_0\bigr)^2\bigl(2 + \xi_0\bigr) - 2S(r)\,\xi_0 = 0.} \tag{53}$$

Applying Viète's trigonometric depressed-cubic formula with $a(S) \equiv \frac{3}{3+2S} \in (0, 1]$ gives the explicit, closed-form physical root $\xi_0(S) \in (0, 1]$ at every radius $r$ without numerical root-finding:

$$\boxed{\xi_0(S) = \frac{2}{\sqrt{a}}\sin\!\left(\frac{1}{3}\arcsin\!\bigl(a^{3/2}\bigr)\right), \qquad a = \frac{3}{3 + 2S}.} \tag{54}$$

Near the stagnation axis $r \to 0$ ($S \to 0, a \to 1$), $\xi_0 \to 1 - \sqrt{2S/3}$ so $G(0) = 2\tau_y/h$ remains completely finite (no singularity!). In the Newtonian high-rate limit $S \to \infty$, $\xi_0 \sim 1/S$, recovering $G(r) = 6\mu_p r W/h^3$.

#### Step 3 — Exact Radial Pressure Profile & Dimensionless Clamping Force $\Phi(\Lambda)$
To integrate $G(r) = -\partial p/\partial r = 2\tau_y/(h\xi_0)$ analytically, we change variables from $r$ to $\xi = \xi_0(\Lambda r/R)$ using Eq. (53), $S(\xi) = \frac{1}{2}(\xi^{-1} - \frac{3}{2} + \frac{1}{2}\xi^2)$ and $\frac{dS}{d\xi} = -\frac{(1-\xi)(1+2\xi)}{2\xi^2}$:

$$p(r) - p_\infty = \int_r^R \frac{2\tau_y}{h\,\xi_0(S(r'))}\,dr' = \frac{2\tau_y R}{h\,\Lambda}\int_{S(r)}^\Lambda \frac{dS'}{\xi_0(S')} = \boxed{\frac{2\tau_y R}{h\,\Lambda}\Bigl[\mathcal{K}\bigl(\xi_0(\Lambda)\bigr) - \mathcal{K}\bigl(\xi_0(\Lambda r/R)\bigr)\Bigr],} \tag{55}$$

where the exact antiderivative is $\mathcal{K}(\xi) = \frac{(1-\xi)^2(1+2\xi)}{2\xi^2}$. Integrating the pressure over the disk by parts ($F = \int_0^R p\,2\pi r\,dr = \pi\int_0^R r^2 G(r)\,dr$) yields:

$$\boxed{F = \frac{2\pi\tau_y R^3}{3h}\,\Phi(\Lambda), \qquad \Phi(\Lambda) \equiv 3\int_0^1 \frac{s^2}{\xi_0(\Lambda s)}\,ds = \frac{3}{\Lambda^3}\Bigl[\mathcal{I}(1) - \mathcal{I}\bigl(\xi_0(\Lambda)\bigr)\Bigr],} \tag{56}$$

where $\mathcal{I}(\xi)$ is the closed-form polynomial/logarithmic antiderivative of $S(\xi)^2(\xi^{-3}-1)$ implemented in `src/rheology_models.py`:

$$\mathcal{I}(\xi) = -\frac{1}{4\xi^4} + \frac{1}{\xi^3} - \frac{9}{8\xi^2} + \frac{3}{2}\ln\xi - \frac{9}{4}\xi - \frac{3}{8}\xi^2 + \frac{1}{2}\xi^3 - \frac{1}{20}\xi^5. \tag{57}$$

#### Step 4 — Asymptotic Limits and Plastic Stall ($h^*, R^*$)
Expanding $\Phi(\Lambda)$ in its two physical limits reveals the complete viscoplastic crossover:

1. **Viscous / Newtonian Limit ($\Lambda \gg 1$, $Bn \ll 1$):** Since $\xi_0(S)^{-1} = S + \frac{3}{2} + \mathcal{O}(S^{-1/2})$,

$$\Phi(\Lambda) \simeq 3\int_0^1 s^2\left(\Lambda s + \frac{3}{2}\right)ds = \frac{3}{4}\Lambda + \frac{3}{2} \implies F \simeq \frac{3\pi\mu_p W R^4}{2h^3} + \frac{\pi\tau_y R^3}{h}, \tag{58}$$

recovering Stefan's Newtonian force (30) plus the leading yield-stress correction.

2. **Plastic Stall Limit ($\Lambda \to 0$, $W \to 0$, $Bn \to \infty$):** As the paste thins and slows down, $\xi_0 \to 1$ across the entire gap and $\Phi(0) = 3\int_0^1 s^2\,ds = 1$. The pressure profile (55) reduces to a linear cone $p(r) - p_\infty = \frac{2\tau_y}{h}(R - r)$, and the clamping force $F_0$ balances the yield stress statically at a finite **stall thickness $h^* > 0$**:

$$F_0 = \frac{2\pi\tau_y (R^*)^3}{3h^*}. \tag{59}$$

Depending on whether $R^*$ reaches $R_{\text{die}}$ before stalling, two distinct stall regimes occur:

$$\boxed{h^* = \begin{cases}
h_{\text{vol}}^* = \left(\dfrac{2\tau_y V_0^{3/2}}{3\sqrt{\pi}F_0}\right)^{2/5}, \quad R^* = \sqrt{\dfrac{V_0}{\pi h_{\text{vol}}^*}}, & \text{if } R^* < R_{\text{die}} \text{ (under-coverage stall)}, \\[10pt]
h_{\text{area}}^* = \dfrac{2\pi\tau_y R_{\text{die}}^3}{3F_0}, \quad R^* = R_{\text{die}}, & \text{if } R_{\text{vol}}^* \ge R_{\text{die}} \text{ (full-coverage stall)}.
\end{cases}} \tag{60}$$

Setting $h_{\text{vol}}^* = h_c = V_0/A_{\text{die}} = V_0/(\pi R_{\text{die}}^2)$ (or equivalently setting $R^* = R_{\text{die}}$ in the area-stall balance $F_0 = 2\pi\tau_y R_{\text{die}}^3/(3h_c)$) identifies the exact critical yield stress $\tau_{y,\text{crit}}$ above which the paste permanently stalls before covering the die:

$$\boxed{\tau_{y,\text{crit}} = \frac{3 F_0 h_c}{2\pi R_{\text{die}}^3} = \frac{3 F_0 V_0}{2\pi^2 R_{\text{die}}^5} = 2812.8\,\text{Pa} \;\; (\approx 2.81\,\text{kPa})} \quad (\text{for our 700 W GPU with } F_0 = 400\,\text{N},\; V_0 = 50\,\text{mm}^3). \tag{61}$$

### 4.4 The Bingham Squeeze-Flow Paradox (Lipscomb & Denn 1984)

A subtle and celebrated continuum-mechanics insight arises when we examine the full 2D rate-of-deformation tensor $\underline{\underline{D}}$ inside the unyielded core $|\zeta| < z_0(r)$ [7]. In standard 1D parallel channel flow, the plug translates at a spatially uniform speed $u_{\text{plug}} = \text{const}$, so every component of $\underline{\underline{D}}$ vanishes identically inside the plug. In radial squeeze flow, however, mass conservation (6) forces the depth-averaged velocity—and therefore the plug speed $u_{\text{plug}}(r)$ in Eq. (49)—to increase with radius $r$ ($\partial u_{\text{plug}}/\partial r > 0$). By incompressibility (7), radial stretching $D_{rr} = \partial u_{\text{plug}}/\partial r > 0$ and hoop stretching $D_{\theta\theta} = u_{\text{plug}}/r > 0$ must be accompanied by vertical compression $D_{zz} = \partial u_z/\partial z < 0$. Consequently, the second invariant of the strain-rate tensor inside the core is non-zero:

$$\dot{\gamma}_{\text{II}} = \sqrt{2\underline{\underline{D}}:\underline{\underline{D}}} = \sqrt{2\left(D_{rr}^2 + D_{\theta\theta}^2 + D_{zz}^2\right) + 4D_{rz}^2} = \mathcal{O}\!\left(\frac{W}{h}\right) = \mathcal{O}(\epsilon\,\dot{\gamma}_w) \ne 0 \quad \text{at } \zeta = 0. \tag{62}$$

Thus, a strictly rigid plug ($D_{ij} \equiv 0$) cannot exist anywhere while the plates are moving ($W > 0$). Asymptotic expansion in $\epsilon = h/R \ll 1$ resolves this paradox: the region $|\zeta| \le z_0(r)$ is a **weakly deforming pseudo-plug** where $|\tau_{rz}| \le \tau_y$ and the extra normal stresses $\tau_{rr}, \tau_{\theta\theta}, \tau_{zz} \sim \mathcal{O}(\tau_y)$ raise the total invariant $\tau_{\text{II}}$ just above $\tau_y$ by $\mathcal{O}(\epsilon)$, permitting slow biaxial extensional flow while leaving the leading-order lubrication velocity (49), pressure (55), and force (56) unchanged to $\mathcal{O}(\epsilon)$. Furthermore, in the static stall limit $W \to 0$, $D_{ij} \to 0$ everywhere, so the plastic stall thickness $h^*$ in Eq. (60) is *exact*.

---

## 5. Dimensional Analysis via Buckingham $\Pi$ Theorem

Following Deck 3 (Slides 3–8, 13–16, 50–53), we organize the physical variables governing constant-volume viscoplastic squeeze flow into a dimensional matrix over the $r = 3$ fundamental mechanical dimensions $\{M, L, T\}$:

$$f\bigl(F,\, h,\, R,\, W,\, \rho,\, \mu_p,\, \tau_y\bigr) = 0 \quad (n = 7 \text{ dimensional variables}). \tag{63}$$

### Table 3: Dimensional Matrix for Viscoplastic Squeeze Flow (Deck 3, Slides 4, 13–15)

| Base Dimension | $F$ | $h$ | $R$ | $W$ | $\rho$ | $\mu_p$ | $\tau_y$ |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Mass ($M$) | $1$ | $0$ | $0$ | $0$ | $1$ | $1$ | $1$ |
| Length ($L$) | $1$ | $1$ | $1$ | $1$ | $-3$ | $-1$ | $-1$ |
| Time ($T$) | $-2$ | $0$ | $0$ | $-1$ | $0$ | $-1$ | $-2$ |

Because the $3\times 3$ submatrix formed by $\{h, W, \mu_p\}$ has determinant $-1 \ne 0$, the rank is $r = 3$. By Buckingham's $\Pi$ theorem (Deck 3, Slide 15), there are $n - r = 7 - 3 = 4$ independent dimensionless groups (plus the dimensionless flow index $n$ when the power-law model is included):

$$\begin{aligned}
\Pi_1 &= \epsilon \equiv \frac{h}{R} && (\text{geometric aspect ratio: thin-gap scale } \ll 1), \\
\Pi_2 &= Re_{\text{sq}} \equiv \frac{\rho W h}{\mu_{\text{eff}}} && (\text{Squeeze Reynolds number: inertia / viscosity } \ll 1), \\
\Pi_3 &= Bn \equiv \frac{\tau_y h^2}{\mu_p R W} = \frac{3}{\Lambda} && (\text{Bingham number: yield stress / viscous wall stress}), \\
\Pi_4 &= \Pi_F \equiv \frac{F h^3}{\mu_p W R^4} = \frac{3\pi}{2}\frac{\Phi(\Lambda)}{\Lambda} && (\text{normalised clamping force relative to viscous scale}).
\end{aligned} \tag{64–67}$$

---

## 6. Energy Transport: 1D Fourier Conduction and Air-Gap Network

Once the mechanical squeeze history $(h(t), R(t))$ is known, we determine the thermal performance of the 700 W GPU package using Fourier's law of heat conduction $\vec{q} = -k\nabla T$ (Deck 1, Slides 48–50; Deck 3, Slides 23–26, 52). Because the bondline aspect ratio $\epsilon = h/R_{\text{die}} \sim 10^{-3} \ll 1$, heat conduction across the TIM layer is purely one-dimensional in $z$:

$$\frac{d^2 T}{dz^2} = 0 \implies q_z'' = -k\frac{dT}{dz} = \frac{k\,\Delta T}{h}. \tag{68}$$

When the paste radius $R(t)$ is smaller than the die radius $R_{\text{die}}$, the die surface $A_{\text{die}} = \pi R_{\text{die}}^2$ is partitioned into two parallel thermal conduction paths across the gap $h(t)$:

1. **Wetted TIM Core ($0 \le r \le R(t)$):** Area $A_{\text{cov}}(t) = \pi\bigl[\min(R(t), R_{\text{die}})\bigr]^2$ with thermal resistance

$$R_{\text{cov}}(t) = \frac{h(t)}{k_{\text{TIM}}\,A_{\text{cov}}(t)}. \tag{69}$$

2. **Unwetted Peripheral Air Annulus ($R(t) < r \le R_{\text{die}}$):** Area $A_{\text{unc}}(t) = A_{\text{die}} - A_{\text{cov}}(t)$ filled with stagnant trapped air ($k_{\text{air}} = 0.026\,\text{W/(m}\cdot\text{K)}$), giving parallel resistance

$$R_{\text{air}}(t) = \frac{h(t)}{k_{\text{air}}\,A_{\text{unc}}(t)}. \tag{70}$$

Combining the two parallel conductances ($R_{\text{TIM,eff}}^{-1} = R_{\text{cov}}^{-1} + R_{\text{air}}^{-1}$) yields the effective package TIM thermal resistance and die-average temperature rise $\Delta T_{\text{TIM}}(t)$ implemented in `src/thermal_coupling.py`:

$$\boxed{R_{\text{TIM,eff}}(t) = \frac{h(t)}{k_{\text{TIM}}\,A_{\text{cov}}(t) + k_{\text{air}}\bigl(A_{\text{die}} - A_{\text{cov}}(t)\bigr)}, \qquad \Delta T_{\text{TIM}}(t) = \dot{Q}\,R_{\text{TIM,eff}}(t).} \tag{71}$$

Furthermore, because the silicon die generates a uniform local heat flux $q'' = \dot{Q}/A_{\text{die}} = 86.0\,\text{W/cm}^2$, any uncovered die perimeter ($R(t) < R_{\text{die}}$) experiences a severe local 1D conduction bottleneck across the air gap:

$$\boxed{\Delta T_{\text{hotspot}}(t) = \frac{q''\,h(t)}{k_{\text{air}}} \quad (\text{when } R(t) < R_{\text{die}}),} \tag{72}$$

which drives localized silicon junction temperatures above thermal-throttling thresholds unless 100% die coverage ($A_{\text{cov}} = A_{\text{die}}$) is achieved.

---

## 7. Results, Visual Analysis, and Verification

### 7.1 Automated Physics Verification Suite

Before generating any figures, all equations in `src/rheology_models.py` and `src/thermal_coupling.py` were subjected to the 20-check automated test suite in `src/diagnostics.py` (implementing the 7-point checklist from Deck 1, Slide 83). As summarized in Table 4, all 20 checks pass to machine or high quadrature precision.

#### Table 4: Summary of the 20 Automated Physics Verification Checks (`python src/verify_physics.py`)

| # | Verification Check Description | Measured Error | Tolerance | Status |
|:---:|---|:---:|:---:|:---:|
| 1 | Power-law limiting case ($n=1, K=\mu$) reproduces Stefan's Newtonian $[h(t), p(r), u_r(r,z), \dot{h}]$ | $4.35\times 10^{-16}$ | $10^{-12}$ | PASS |
| 2 | Bingham limiting case ($\tau_y = 10^{-3}\,\text{Pa} \to 0$) reproduces Newtonian $[h(t), p(r), \dot{h}]$ | $6.87\times 10^{-6}$ | $10^{-4}$ | PASS |
| 3 | Bingham nominal ($\tau_y = 250\,\text{Pa}$): $h(t\to\infty) \to h_{\text{area}}^* = 5.46\,\mu\text{m}$ (constant-area stall) | $1.73\times 10^{-9}$ | $10^{-3}$ | PASS |
| 4 | Bingham nominal ($\tau_y = 250\,\text{Pa}$): static plastic-limit force at $(h^*, R^*)$ equals $F_0$ | $0.00\times 10^{0}$ | $10^{-12}$ | PASS |
| 5 | Bingham high-yield ($\tau_y = 5\,\text{kPa}$): $h(t\to\infty) \to h_{\text{vol}}^* = 77.32\,\mu\text{m}$ (under-coverage stall) | $0.00\times 10^{0}$ | $10^{-3}$ | PASS |
| 6 | Bingham high-yield ($\tau_y = 5\,\text{kPa}$): static plastic-limit force at $(h^*, R^*)$ equals $F_0$ | $1.11\times 10^{-15}$ | $10^{-12}$ | PASS |
| 7 | Critical yield stress $\tau_{y,\text{crit}} = 3F_0 h_c/(2\pi R_{\text{die}}^3) = 2812.8\,\text{Pa}$ & $h_{\text{vol}}^*(\tau_{y,\text{crit}}) = h_c$ | $6.66\times 10^{-16}$ | $10^{-9}$ | PASS |
| 8 | Power-law ODE vs. closed-form $h(60\,\text{s})$ for $n=0.5$ ($10.77\,\mu\text{m}$) | $7.39\times 10^{-11}$ | $10^{-6}$ | PASS |
| 9 | Power-law ODE vs. closed-form $h(60\,\text{s})$ for $n=1.0$ ($24.62\,\mu\text{m}$) | $5.43\times 10^{-12}$ | $10^{-6}$ | PASS |
| 10 | Power-law ODE vs. closed-form $h(60\,\text{s})$ for $n=1.3$ ($33.04\,\mu\text{m}, t_c = 12.34\,\text{s}$) | $1.50\times 10^{-11}$ | $10^{-6}$ | PASS |
| 11 | Bingham ordering: $h_{\text{Bingham}}(t) \ge h_{\text{Newtonian}}(t)$ ($\mu_p = \mu$) and $h_{\text{Bingham}}(t) \ge h^*$ for all $t$ | $0.00\times 10^{0}$ | $10^{-12}$ | PASS |
| 12 | Global volume conservation $\pi R(t)^2 h(t) = V_0$ in Phase 1 ($\le V_0$ in Phase 2) across all models | $3.97\times 10^{-16}$ | $10^{-12}$ | PASS |
| 13 | Integral axial force balance $\int_0^R [p(r)-p_\infty]2\pi r\,dr = F_0$ along all trajectories | $4.09\times 10^{-9}$ | $10^{-6}$ | PASS |
| 14 | RTT radial flux continuity $\int_0^h u_r(r,z)\,dz = r(-\dot{h})/2$ across all models and radii | $2.89\times 10^{-14}$ | $10^{-6}$ | PASS |
| 15 | Bingham constitutive consistency: $\lvert\tau_{rz}\rvert \le \tau_y$ inside core, flat plug velocity, exact cubic root | $6.38\times 10^{-16}$ | $10^{-9}$ | PASS |
| 16 | Asymptotic constant-volume scaling $h \propto t^{-2n/(3n+5)}$ for $n=1.0$ (expected $-0.25000$) | $2.92\times 10^{-11}$ | $10^{-3}$ | PASS |
| 17 | Asymptotic constant-volume scaling $h \propto t^{-2n/(3n+5)}$ for $n=0.5$ (expected $-0.15385$) | $1.11\times 10^{-15}$ | $10^{-3}$ | PASS |
| 18 | Asymptotic constant-volume scaling $h \propto t^{-2n/(3n+5)}$ for $n=1.3$ (expected $-0.29213$) | $3.43\times 10^{-10}$ | $10^{-3}$ | PASS |
| 19 | Dimensional homogeneity: $h(t)$ invariant under arbitrary rescaling of base units $(M, L, T)$ | $6.92\times 10^{-16}$ | $10^{-6}$ | PASS |
| 20 | Parallel thermal resistance network limits ($100\%$ TIM coverage vs. $0\%$ air-only limit) | $1.77\times 10^{-16}$ | $10^{-9}$ | PASS |

### 7.2 Velocity, Shear Stress, and Pressure Profiles (Figures 1 and 2)

Figure 1 compares the normalized cross-gap radial velocity profiles $u_r(z)/\bar{u}_r$ and shear-stress distributions $\tau_{rz}(z)/\tau_w$ at the identical volumetric flux $\bar{u}_r = rW/(2h)$. As derived in Eq. (26), the Newtonian paste exhibits a classic Poiseuille parabola peaking at $u_{\max}/\bar{u}_r = 1.5$. Decreasing the power-law index to $n=0.4$ (shear-thinning) blunts the core profile ($u_{\max}/\bar{u}_r = \frac{2n+1}{n+1} = 1.286$) and concentrates shear near the walls, whereas $n=1.3$ (shear-thickening) sharpens the peak to $1.565$. The Bingham plastic ($\xi_0 = 0.50$) exhibits a completely flat central translation zone $|z/h - 0.5| \le 0.25$ where $|\tau_{rz}| \le \tau_y$ (Fig. 1b), confirming that the linear shear stress $\tau_{rz} = -G(z - h/2)$ is universal while the velocity response is governed by constitutive closure.

![Figure 1: Cross-gap velocity profiles and universal linear shear-stress profiles](../figures/fig1_velocity_stress.png)  
*Figure 1: Cross-gap velocity profiles $u_r(z)/\bar{u}_r$ (a) and universal linear shear-stress profiles $\tau_{rz}(z)/\tau_w$ (b) across Newtonian, power-law ($n \in \{0.4, 0.7, 1.3\}$), and Bingham ($\xi_0 = 0.50$) models at identical radial volumetric flux.*

Figure 2a displays the normalized radial pressure distributions $(p(r)-p_\infty)/p_{\text{ref}}$ across the disk radius $r/R$. The Newtonian parabola $1-(r/R)^2$ transitions to a fuller dome $1-(r/R)^{n+1}$ for shear-thickening paste and a flatter profile for shear-thinning paste, while approaches to the Bingham plastic limit ($\Lambda \to 0$) converge toward the linear plastic cone $p(r)-p_\infty = \frac{2\tau_y}{h}(R-r)$. Figure 2b maps these radial pressure profiles directly onto the 700 W AI GPU die footprint ($R_{\text{die}} = 16.10\,\text{mm}$) at $t = 60\,\text{s}$, illustrating how the high-yield Bingham paste ($\tau_y = 5\,\text{kPa}$) stalls at $R^* = 14.35\,\text{mm}$ ($79.4\%$ area coverage), leaving an exposed peripheral ring of bare silicon.

![Figure 2: Normalized radial pressure distributions and physical gauge pressure across the 700 W AI GPU die](../figures/fig2_pressure_coverage.png)  
*Figure 2: Normalized radial pressure distributions $(p(r)-p_\infty)/p_{\text{ref}}$ (a) and top-down 700 W AI GPU die coverage ($R_{\text{die}} = 16.10\,\text{mm}$) (b), highlighting the uncovered die annulus ($R^* = 14.35\,\text{mm}$) for the high-yield Bingham paste.*

### 7.3 Bondline Thinning Dynamics and Pseudo-Plug Morphology (Figures 3 and 4)

Figure 3 tracks the temporal evolution of bondline thickness $h(t)$ (log–log scale, Fig. 3a) and normalized spread radius $R(t)/R_{\text{die}}$ (Fig. 3b) over $t \in [10^{-3}, 200]\,\text{s}$. During Phase 1 ($h > h_c = 61.43\,\mu\text{m}$), the Newtonian and power-law trajectories follow their exact constant-volume scaling slopes $h \propto t^{-2n/(3n+5)}$, before steepening to $h \propto t^{-n/(n+1)}$ upon reaching $100\%$ die coverage ($h = h_c$, reached at $t_c = 0.14\,\text{s}$ for $n=0.5$, $4.89\,\text{s}$ for Newtonian $n=1.0$, and $12.34\,\text{s}$ for $n=1.3$). Because wall shear rates $\dot{\gamma}_w \sim RW/h^2$ exceed $10^2\,\text{s}^{-1}$ during early compression, the shear-thinning paste ($n=0.5$) experiences an order-of-magnitude viscosity drop, reaching full die coverage in $0.14\,\text{s}$ and thinning to $h(60\,\text{s}) = 10.77\,\mu\text{m}$. The nominal Bingham paste ($\tau_y = 250\,\text{Pa}, \mu_p = 100\,\text{Pa}\cdot\text{s}$) always remains thicker than the Newtonian paste of equal viscosity ($h(60\,\text{s}) = 27.45\,\mu\text{m} > 24.62\,\mu\text{m}$) because $F_{\text{Bingham}}(W,h) > F_{\text{Newtonian}}(W,h)$ at every state, asymptotically approaching its constant-area stall thickness $h_{\text{area}}^* = 5.46\,\mu\text{m}$ only as $t \to \infty$. In contrast, the high-yield Bingham paste ($\tau_y = 5\,\text{kPa} > \tau_{y,\text{crit}} = 2.81\,\text{kPa}$) plateaus horizontally onto its exact constant-volume plastic stall asymptote $h_{\text{vol}}^* = 77.32\,\mu\text{m}$ at $79.4\%$ coverage ($h(60\,\text{s}) = 78.39\,\mu\text{m}$, within $1.4\%$ of $h_{\text{vol}}^*$).

![Figure 3: Constant-force squeeze dynamics on the 700 W GPU die](../figures/fig3_thickness_radius.png)  
*Figure 3: Constant-force ($F_0 = 400\,\text{N}$) squeeze dynamics on the 700 W GPU die: (a) log–log bondline trajectory $h(t)$ showing the Phase 1 $\to$ Phase 2 kink at $h_c = 61.43\,\mu\text{m}$ and Bingham plastic stall asymptotes $h^*$; (b) radial spreading front $R(t)/R_{\text{die}}$ and die-perimeter capping.*

Figure 4a visualizes the 2D $(r,z)$ internal structure of the Bingham pseudo-plug zone $|\zeta| \le z_0(r) = \xi_0(r)h/2$ inside the gap. At the axis of symmetry $r=0$, the radial flux vanishes ($S(0)=0 \implies \xi_0(0)=1$), so the unyielded core spans the entire gap thickness ($2z_0 = h$). Moving radially outward, the rising volumetric flux $q_r = rW/2$ increases $S(r)$ and thins the pseudo-plug core toward the rim $r=R$. Figure 4b tracks the growth of the local plug fraction $\xi_0(r)$ as $h(t) \to h^*$, demonstrating the lock-up transition toward $\xi_0 \equiv 1$ across the entire die.

![Figure 4: 2D Bingham pseudo-plug zone map and yield-surface evolution toward stall](../figures/fig4_bingham_plug_map.png)  
*Figure 4: Bingham yield-stress mechanics: (a) 2D cross-sectional map of the unyielded pseudo-plug core $|z - h/2| \le z_0(r)$ across the gap; (b) growth of the unyielded plug fraction $\xi_0(r)$ as $h(t) \to h^*$.*

### 7.4 GPU Thermal Design Maps and Dimensionless Validity (Figures 5 and 6)

Table 5 and Figure 5 synthesize the coupled thermo-mechanical design space for the 700 W AI GPU at $t = 60\,\text{s}$. In the Bingham design plane $(F_0, \tau_y)$ (Fig. 5a), the white dashed critical locus

$$F_{\text{crit}}(\tau_y) = \frac{2\pi R_{\text{die}}^3}{3h_c}\tau_y = \frac{2\pi^2 R_{\text{die}}^5}{3V_0}\tau_y \tag{73}$$

(or equivalently $\tau_{y,\text{crit}}(F_0) = \frac{3F_0 V_0}{2\pi^2 R_{\text{die}}^5}$, equal to $2.81\,\text{kPa}$ at $F_0 = 400\,\text{N}$) separates safe full-coverage packaging (lower-right region, $\tau_y \le \tau_{y,\text{crit}}$) from partial-coverage stall (upper-left region, $\tau_y > \tau_{y,\text{crit}}$). Crossing this boundary from the nominal Bingham paste ($\tau_y = 250\,\text{Pa}$, $100\%$ coverage, $h(60\,\text{s}) = 27.45\,\mu\text{m}$, $\Delta T_{\text{TIM}} = 4.72\,\text{K}$) to the high-yield Bingham paste ($\tau_y = 5\,\text{kPa}$, stalled at $h^* = 77.32\,\mu\text{m}$, $R^* = 14.35\,\text{mm}$, $79.4\%$ coverage) causes $\Delta T_{\text{TIM}}$ to jump steeply from $4.72\,\text{K}$ to $16.71\,\text{K}$ at the stall limit ($17.18\,\text{K}$ at $t = 60\,\text{s}$ where $h(60\,\text{s}) = 78.39\,\mu\text{m}$), accompanied by a local 1D air-gap perimeter hotspot of $\Delta T_{\text{hotspot}} = q'' h^*/k_{\text{air}} = 2557.2\,\text{K}$. Figure 5b maps the power-law design plane $(n, V_0)$, showing that shear-thinning formulations ($n = 0.5$, $h(60\,\text{s}) = 10.77\,\mu\text{m}$, $\Delta T_{\text{TIM}} = 1.85\,\text{K}$) cut final bondline thermal resistance by $56\%$ relative to a Newtonian paste ($h(60\,\text{s}) = 24.62\,\mu\text{m}$, $\Delta T_{\text{TIM}} = 4.23\,\text{K}$), whereas shear-thickening paste ($n = 1.3$, $t_c = 12.34\,\text{s}$) thins more slowly to $h(60\,\text{s}) = 33.04\,\mu\text{m}$ ($\Delta T_{\text{TIM}} = 5.68\,\text{K}$, $R_{\text{TIM,eff}} = 0.00812\,\text{K/W}$).

#### Table 5: 700 W AI GPU Bondline & Thermal Performance Summary at $t = 60\,\text{s}$ ($F_0 = 400\,\text{N}$, $V_0 = 50\,\text{mm}^3$, $h_0 = 1.0\,\text{mm}$)

*Note: For the high-yield Bingham paste ($\tau_y = 5\,\text{kPa}$), values shown are the exact plastic stall limit ($h^*, R^*$); at $t = 60\,\text{s}$ the trajectory is within $1.4\%$ of stall ($h(60\,\text{s}) = 78.39\,\mu\text{m}$, $R(60\,\text{s}) = 14.25\,\text{mm}$, $78.4\%$ coverage, $\Delta T_{\text{TIM}} = 17.18\,\text{K}$).*

| TIM Rheological Model | $h(60\,\text{s})$ [$\mu\text{m}$] | $R(60\,\text{s})$ [$\text{mm}$] | Coverage [%] | $R_{\text{TIM,eff}}$ [$\text{K/W}$] | $\Delta T_{\text{TIM}}$ [$\text{K}$] | $\Delta T_{\text{hotspot}}$ [$\text{K}$] |
|---|---:|---:|---:|---:|---:|---:|
| Shear-Thinning ($n=0.5, K=100\,\text{Pa}\cdot\text{s}^{0.5}$) | $10.77$ | $16.10$ | $100.0\%$ | $0.00265$ | $1.85$ | $0.0$ |
| Newtonian Reference ($\mu = 100\,\text{Pa}\cdot\text{s}$) | $24.62$ | $16.10$ | $100.0\%$ | $0.00605$ | $4.23$ | $0.0$ |
| Bingham Nominal ($\tau_y = 250\,\text{Pa}, \mu_p = 100\,\text{Pa}\cdot\text{s}$) | $27.45$ | $16.10$ | $100.0\%$ | $0.00675$ | $4.72$ | $0.0$ |
| Shear-Thickening ($n=1.3, K=100\,\text{Pa}\cdot\text{s}^{1.3}$) | $33.04$ | $16.10$ | $100.0\%$ | $0.00812$ | $5.68$ | $0.0$ |
| Bingham High-Yield Stall ($\tau_y = 5\,\text{kPa}$, stall $h^*$) | $77.32$ ($h^*$) | $14.35$ ($R^*$) | $79.4\%$ | $0.02387$ | $16.71$ | $2557.2$ |

![Figure 5: 700 W AI GPU thermal design maps of Delta T_TIM at t = 60 s](../figures/fig5_gpu_thermal_design_map.png)  
*Figure 5: 700 W AI GPU thermal design maps of $\Delta T_{\text{TIM}}$ at $t = 60\,\text{s}$: (a) Bingham clamping force $F_0$ vs. yield stress $\tau_y$, with the exact critical full-coverage boundary $F_{\text{crit}}(\tau_y) = \frac{2\pi^2 R_{\text{die}}^5}{3V_0}\tau_y$ ($\tau_{y,\text{crit}} = 2.81\,\text{kPa}$ at $F_0 = 400\,\text{N}$); (b) power-law flow index $n$ vs. dispensed volume $V_0$.*

Finally, Figure 6 provides an explicit a-posteriori check of our two foundational simplifying assumptions across all five trajectories. Figure 6a confirms that the aspect ratio $\epsilon(t) = h(t)/R(t)$ remains between $10^{-3}$ and $10^{-2}$ (more than $10\times$ below the $\epsilon = 0.1$ lubrication breakdown threshold) and the squeeze Reynolds number $Re_{\text{sq}}(t)$ remains between $10^{-12}$ and $10^{-5}$ (more than $10^4\times$ below unity). Figure 6b tracks the Bingham number $Bn(t) = \tau_y h^2/(\mu_p R |\dot{h}|)$, showing its smooth crossover from the viscous-dominated regime ($Bn \ll 1$) at early times to plastic-stall divergence ($Bn \to \infty$ as $|\dot{h}| \to 0$ and $h \to h^*$).

![Figure 6: Dimensionless assumption-validity trajectories](../figures/fig6_regime_validity.png)  
*Figure 6: Dimensionless assumption-validity trajectories over $t \in [10^{-3}, 100]\,\text{s}$: (a) geometric aspect ratio $\epsilon(t) = h(t)/R(t) \ll 1$ and squeeze Reynolds number $Re_{\text{sq}}(t) \ll 1$; (b) Bingham number $Bn(t)$ divergence as $h(t) \to h^*$.*

---

## 8. Engineering Design Conclusions for Semiconductor Packaging

1. **Shear-Thinning ($n < 1$) Accelerates Compression Without Sacrificing Stability at Rest:** Because the characteristic shear rate $\dot{\gamma}_c = RW/h^2$ scales inversely with $h^2$, a shear-thinning paste ($n=0.5$) flows rapidly under initial clamping ($h(60\,\text{s}) = 10.77\,\mu\text{m}$, $\Delta T_{\text{TIM}} = 1.85\,\text{K}$ at $60\,\text{s}$, a $56\%$ reduction vs. Newtonian paste at $24.62\,\mu\text{m}$ and $4.23\,\text{K}$) while recovering high viscosity once motion ceases. Conversely, a Bingham paste with the same plastic viscosity ($\mu_p = \mu = 100\,\text{Pa}\cdot\text{s}, \tau_y = 250\,\text{Pa}$) squeezes more slowly ($h(60\,\text{s}) = 27.45\,\mu\text{m}, \Delta T_{\text{TIM}} = 4.72\,\text{K}$) because its yield stress opposes compression at every instant before asymptotically approaching $h_{\text{area}}^* = 5.46\,\mu\text{m}$ as $t \to \infty$.
2. **Yield Stress Imposes a Hard Plastic Stall Limit $h^*$:** Increasing filler loading to boost $k_{\text{TIM}}$ inevitably raises the yield stress $\tau_y$. If $\tau_y$ exceeds $\tau_{y,\text{crit}} = \frac{3F_0 h_c}{2\pi R_{\text{die}}^3} = \frac{3F_0 V_0}{2\pi^2 R_{\text{die}}^5} = 2.81\,\text{kPa}$ (at $F_0 = 400\,\text{N}$, $V_0 = 50\,\text{mm}^3$), the paste stalls before reaching the die perimeter ($R^* < R_{\text{die}}$). The resulting peripheral air gap degrades package thermal performance far more severely than any gain in bulk $k_{\text{TIM}}$.
3. **Actionable Assembly Remedy:** To prevent Bingham under-coverage on large-area AI GPU dies without exceeding mechanical die-cracking load limits ($F_0 \le 400\text{–}600\,\text{N}$), packaging engineers should either (i) formulate the paste with dispersants to keep $\tau_y \le 500\,\text{Pa}$ while relying on shear-thinning ($n \approx 0.4\text{–}0.6$), or (ii) switch from a single central pea-dot to a multi-dot / cross-pattern stencil dispense that reduces the effective radial travel distance $R_{\text{eff}}$.

---

## References

1. S. Bhattacharyya, *Course Lecture Slides: (1) Conservation and Transport Equations; (2) Momentum, Energy and Fluid Flow; (3) Dimensionless Numbers as Ratios of Physical Effects*, Department of Materials Science and Metallurgical Engineering, IIT Hyderabad, 2026.
2. J. R. Welty, C. E. Wicks, R. E. Wilson, and G. L. Rorrer, *Fundamentals of Momentum, Heat, and Mass Transfer*, 5th ed. Hoboken, NJ: John Wiley & Sons, 2008, chs. 4–11, 15.
3. R. B. Bird, W. E. Stewart, and E. N. Lightfoot, *Transport Phenomena*, 2nd ed. New York: John Wiley & Sons, 2007.
4. J. Stefan, "Versuche über die scheinbare Adhäsion," *Sitzungsber. Kaiserl. Akad. Wiss. Wien, Math.-Naturwiss. Kl.*, vol. 69, pp. 713–735, 1874.
5. J. R. Scott, "Theory and application of the parallel-plate plastimeter," *Trans. Inst. Rubber Ind.*, vol. 7, pp. 169–186, 1931.
6. G. H. Covey and B. R. Stanmore, "Use of the parallel-plate plastometer for the characterisation of viscous fluids with a yield stress," *J. Non-Newtonian Fluid Mech.*, vol. 8, no. 3–4, pp. 249–260, 1981.
7. G. G. Lipscomb and M. M. Denn, "Flow of Bingham fluids in complex geometries," *J. Non-Newtonian Fluid Mech.*, vol. 14, pp. 337–346, 1984.
8. J. Szekely, J. W. Evans, and J. K. Brimacombe, *The Mathematical and Physical Modeling of Primary Metals Processing Operations*. New York: Wiley, 1988, ch. 3.
9. D. R. Poirier and G. H. Geiger, *Transport Phenomena in Materials Processing*. Warrendale, PA: TMS, 1994.

"""
physics_models.py -- Facade over the independent physics components.

Execution hierarchy (one-way, no circular imports)::

    params.py ──► rheology_models.py ──► thermal_coupling.py
         │                 │
         └────────────────►└──► diagnostics.py ──► verify_physics.py
                                         └──► generate_figures.py (Phase 2)
                                                   └──► squeeze_flow_tim.py (Phase 3)

Import everything from one place::

    import physics_models as pm
    res = pm.solve_squeeze(pm.NEWTONIAN, t, pm.GPU_700W.F0, pm.DROPLET.V0,
                           pm.DROPLET.h0, pm.GPU_700W.R_die)
"""
from params import *              # noqa: F401,F403  Component 1
from rheology_models import *     # noqa: F401,F403  Component 2
from thermal_coupling import *    # noqa: F401,F403  Component 3
from diagnostics import *         # noqa: F401,F403  Component 4

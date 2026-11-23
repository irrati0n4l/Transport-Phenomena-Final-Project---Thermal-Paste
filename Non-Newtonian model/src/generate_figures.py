"""
generate_figures.py -- Phase 2 CLI runner for the 6-figure publication suite + GIF.

Generates:
  - figures/fig1_velocity_stress.png / .pdf
  - figures/fig2_pressure_coverage.png / .pdf
  - figures/fig3_thickness_radius.png / .pdf
  - figures/fig4_bingham_plug_map.png / .pdf
  - figures/fig5_gpu_thermal_design_map.png / .pdf
  - figures/fig6_regime_validity.png / .pdf
  - figures/gpu_spread.gif

Usage:
    python src/generate_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from visuals import (FIGURES_DIR, REPO_ROOT, fig1_velocity_stress,
                     fig2_pressure_coverage, fig3_thickness_radius,
                     fig4_bingham_plug_map, fig5_gpu_thermal_design_map,
                     fig6_regime_validity, generate_all_visuals,
                     generate_gpu_spread_gif)

__all__ = [
    "FIGURES_DIR",
    "fig1_velocity_stress",
    "fig2_pressure_coverage",
    "fig3_thickness_radius",
    "fig4_bingham_plug_map",
    "fig5_gpu_thermal_design_map",
    "fig6_regime_validity",
    "generate_gpu_spread_gif",
    "generate_all_visuals",
]


def main() -> int:
    print("=" * 90)
    print("Phase 2 — Generating 6 Publication Figures (300 DPI PNG + Vector PDF) & GPU Spreading GIF")
    print("=" * 90)
    outputs = generate_all_visuals(FIGURES_DIR)
    for p in outputs:
        rel = p.relative_to(REPO_ROOT) if p.is_relative_to(REPO_ROOT) else p
        print(f"  [OK] {str(rel):48s} ({p.stat().st_size / 1024:7.1f} KB)")
    print("-" * 90)
    print(f"Completed: {len(outputs)} visual artifacts written to {FIGURES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

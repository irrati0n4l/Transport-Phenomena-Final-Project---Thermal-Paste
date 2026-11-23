"""
verify_physics.py -- Phase 1 verification runner.

Runs every limiting-case, conservation, constitutive and dimensional check in
``diagnostics.py`` and exits non-zero if any fails (CI friendly).

    python src/verify_physics.py
"""
import sys

from diagnostics import format_checks, run_all_checks
from params import describe


def main() -> int:
    print("=" * 100)
    print("Squeeze-flow TIM model -- physics verification")
    print("=" * 100)
    print(describe())
    print()
    checks = run_all_checks()
    print(format_checks(checks))
    return 0 if all(c.passed for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())

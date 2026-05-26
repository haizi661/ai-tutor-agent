from __future__ import annotations

import argparse
import json

from ai_tutor_agent.infrastructure.matlab_experiment import MatlabExperimentService


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug the local MATLAB experiment chain.")
    parser.add_argument("--status-only", action="store_true", help="Only print MATLAB detection status.")
    parser.add_argument("--gain", type=float, default=1.0)
    parser.add_argument("--time-constant", type=float, default=1.0)
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--step-size", type=float, default=0.02)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args()

    service = MatlabExperimentService()
    print(json.dumps(service.status(), ensure_ascii=False, indent=2))
    if args.status_only:
        return

    result = service.run_first_order_step(
        gain=args.gain,
        time_constant=args.time_constant,
        duration=args.duration,
        step_size=args.step_size,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

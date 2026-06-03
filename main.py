import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Tutor Agent")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    args = parser.parse_args()

    if args.cli:
        from ai_tutor_agent.cli import run_cli
        run_cli()
    else:
        from ai_tutor_agent.interfaces.api.app import run_api
        run_api()


if __name__ == "__main__":
    main()

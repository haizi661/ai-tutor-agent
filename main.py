import sys


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        from ai_tutor_agent.cli import run_cli
        run_cli()
    else:
        from ai_tutor_agent.interfaces.api.app import run_api
        run_api()

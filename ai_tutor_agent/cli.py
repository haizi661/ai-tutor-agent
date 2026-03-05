def run_cli() -> None:
    # Lazy import keeps lightweight modules importable in test/runtime environments
    # where optional CLI dependencies are not installed.
    from .interfaces.cli.app import run_cli as _run_cli

    _run_cli()


__all__ = ["run_cli"]

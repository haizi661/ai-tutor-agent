from __future__ import annotations

import os
import platform
import re
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
from typing import Any


_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_WSL_MOUNT_RE = re.compile(r"^/mnt/([A-Za-z])(?:/(.*))?$")
_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def is_windows_path(value: str | os.PathLike[str] | None) -> bool:
    text = str(value or "").strip()
    return bool(_WINDOWS_DRIVE_RE.match(text)) or text.startswith("\\\\")


def is_wsl() -> bool:
    if os.environ.get("WSL_INTEROP") or os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        release = Path("/proc/sys/kernel/osrelease").read_text(encoding="utf-8").lower()
    except OSError:
        return False
    return "microsoft" in release or "wsl" in release


def runtime_platform() -> str:
    system = platform.system().lower()
    if system.startswith("windows"):
        return "windows"
    if system == "darwin":
        return "macos"
    if is_wsl():
        return "wsl"
    return "linux"


def runtime_info() -> SimpleNamespace:
    label = runtime_platform()
    return SimpleNamespace(
        platform=label,
        is_windows=label == "windows",
        is_wsl=label == "wsl",
        is_macos=label == "macos",
        is_linux=label == "linux",
        is_posix=label in {"wsl", "linux", "macos"},
        path_separator="\\" if label == "windows" else "/",
    )


def project_root() -> Path:
    return _PROJECT_ROOT


def windows_to_wsl_path(path: str | os.PathLike[str]) -> str:
    text = str(path).strip().strip('"')
    if not text:
        return ""
    if text.startswith("\\\\"):
        # UNC/network paths are not available through /mnt/<drive>; keep unchanged.
        return text
    if not is_windows_path(text):
        return text
    win_path = PureWindowsPath(text)
    drive = win_path.drive.rstrip(":").lower()
    parts = [part for part in win_path.parts[1:] if part not in {"\\", "/"}]
    return "/".join([f"/mnt/{drive}", *parts])


def wsl_to_windows_path(path: str | os.PathLike[str]) -> str:
    text = str(path).strip().strip('"')
    match = _WSL_MOUNT_RE.match(text)
    if not match:
        return text
    drive = match.group(1).upper()
    rest = match.group(2) or ""
    if not rest:
        return f"{drive}:\\"
    return f"{drive}:\\" + rest.replace("/", "\\")


def adapt_path_for_runtime(path: str | os.PathLike[str], *, runtime: str | None = None) -> str:
    text = str(path).strip().strip('"')
    if not text:
        return ""
    selected = (runtime or runtime_platform()).lower()
    if selected == "wsl" and is_windows_path(text):
        return windows_to_wsl_path(text)
    if selected == "windows" and _WSL_MOUNT_RE.match(text):
        return wsl_to_windows_path(text)
    return text


def runtime_path(path: str | os.PathLike[str], *, runtime: str | None = None) -> Path:
    return Path(adapt_path_for_runtime(path, runtime=runtime)).expanduser()


def resolve_project_path(
    path: str | os.PathLike[str],
    *,
    runtime: str | None = None,
    base_dir: str | Path | None = None,
) -> Path:
    candidate = runtime_path(path, runtime=runtime)
    if candidate.is_absolute():
        return candidate.resolve()
    anchor = Path(base_dir) if base_dir is not None else project_root()
    return (anchor / candidate).resolve()


def _candidate_paths(path: str | os.PathLike[str], *, runtime: str | None = None) -> list[Path]:
    raw = str(path).strip().strip('"')
    adapted = adapt_path_for_runtime(raw, runtime=runtime)
    candidates = [Path(adapted).expanduser()]
    if "\\" in raw and not is_windows_path(raw):
        candidates.append(Path(raw.replace("\\", "/")).expanduser())
    if adapted != raw:
        candidates.append(Path(raw).expanduser())
    if is_windows_path(raw):
        name = PureWindowsPath(raw).name
        if name:
            candidates.append(Path(name))
    return candidates


def resolve_existing_path(path: str | os.PathLike[str], *, base_dir: str | Path | None = None, runtime: str | None = None) -> Path | None:
    for candidate in _candidate_paths(path, runtime=runtime):
        if candidate.is_absolute():
            options = [candidate]
        else:
            options = []
            if base_dir is not None:
                options.append(Path(base_dir) / candidate)
            options.append(project_root() / candidate)
            options.append(candidate)
        for option in options:
            try:
                if option.exists():
                    return option.resolve()
            except OSError:
                continue
    return None


def project_relative_path(path: str | os.PathLike[str] | Path) -> str:
    text = str(path).strip().strip('"')
    if not text:
        return ""
    if not is_windows_path(text):
        candidate = Path(text)
        if not candidate.is_absolute():
            return text.replace("\\", "/")
    candidate = runtime_path(text)
    try:
        resolved = candidate.resolve()
    except OSError:
        resolved = candidate
    try:
        return resolved.relative_to(project_root()).as_posix()
    except ValueError:
        return text.replace("\\", "/")


def normalize_path_value(value: Any, *, runtime: str | None = None) -> Any:
    if isinstance(value, os.PathLike):
        return adapt_path_for_runtime(value, runtime=runtime)
    if isinstance(value, str):
        return adapt_path_for_runtime(value, runtime=runtime)
    return value

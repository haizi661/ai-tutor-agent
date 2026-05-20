from types import SimpleNamespace

from ai_tutor_agent import platform_paths
from ai_tutor_agent.platform_paths import (
    adapt_path_for_runtime,
    is_windows_path,
    project_relative_path,
    project_root,
    resolve_project_path,
    resolve_existing_path,
    runtime_info,
    runtime_platform,
    windows_to_wsl_path,
    wsl_to_windows_path,
)


def test_detects_windows_drive_paths_without_running_on_windows():
    assert is_windows_path(r"C:\Users\haizi\Desktop\course.pdf") is True
    assert is_windows_path("D:/data/mineru_cache/chapter/full.md") is True
    assert is_windows_path("data/mineru_cache/chapter/full.md") is False


def test_converts_windows_drive_path_to_wsl_mount_path():
    assert windows_to_wsl_path(r"C:\Users\haizi\Desktop\course.pdf") == "/mnt/c/Users/haizi/Desktop/course.pdf"
    assert windows_to_wsl_path("D:/data/mineru_cache/chapter/full.md") == "/mnt/d/data/mineru_cache/chapter/full.md"


def test_converts_wsl_mount_path_to_windows_drive_path():
    assert wsl_to_windows_path("/mnt/c/Users/haizi/Desktop/course.pdf") == r"C:\Users\haizi\Desktop\course.pdf"
    assert wsl_to_windows_path("/home/haizi/project/data") == "/home/haizi/project/data"


def test_adapt_path_for_explicit_runtime_is_deterministic():
    assert adapt_path_for_runtime(r"E:\fish\FishConv", runtime="wsl") == "/mnt/e/fish/FishConv"
    assert adapt_path_for_runtime("/mnt/e/fish/FishConv", runtime="windows") == r"E:\fish\FishConv"
    assert adapt_path_for_runtime("data/mineru_cache", runtime="linux") == "data/mineru_cache"
    assert adapt_path_for_runtime("data/mineru_cache", runtime="wsl") == "data/mineru_cache"
    assert adapt_path_for_runtime("data/mineru_cache", runtime="windows") == "data/mineru_cache"
    assert adapt_path_for_runtime("data/mineru_cache", runtime="macos") == "data/mineru_cache"
    assert adapt_path_for_runtime(r"data\mineru_cache\chapter\full.md", runtime="wsl") == r"data\mineru_cache\chapter\full.md"
    assert adapt_path_for_runtime(r"outputs\media\figure.png", runtime="macos") == r"outputs\media\figure.png"
    assert adapt_path_for_runtime("/Users/haizi/course/data", runtime="macos") == "/Users/haizi/course/data"
    assert adapt_path_for_runtime(r"E:\fish\FishConv", runtime="macos") == r"E:\fish\FishConv"


def test_runtime_platform_distinguishes_macos_before_linux(monkeypatch):
    monkeypatch.setattr(platform_paths.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(platform_paths, "is_wsl", lambda: False)

    assert runtime_platform() == "macos"
    info = runtime_info()
    assert info.platform == "macos"
    assert info.is_macos is True
    assert info.is_posix is True
    assert info.path_separator == "/"


def test_runtime_platform_distinguishes_windows(monkeypatch):
    monkeypatch.setattr(platform_paths.platform, "system", lambda: "Windows")
    monkeypatch.setattr(platform_paths, "is_wsl", lambda: False)

    info = runtime_info()
    assert info.platform == "windows"
    assert info.is_windows is True
    assert info.is_posix is False
    assert info.path_separator == "\\"


def test_resolve_existing_path_falls_back_to_filename_for_foreign_windows_abs_path(tmp_path):
    image = tmp_path / "figure.png"
    image.write_bytes(b"image")

    resolved = resolve_existing_path(r"C:\Users\haizi\Desktop\figure.png", base_dir=tmp_path, runtime="linux")

    assert resolved == image.resolve()


def test_resolve_existing_path_prefers_base_dir_for_relative_paths(tmp_path):
    nested = tmp_path / "data" / "mineru_cache" / "chapter" / "full.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("content", encoding="utf-8")

    resolved = resolve_existing_path("data/mineru_cache/chapter/full.md", base_dir=tmp_path, runtime="macos")

    assert resolved == nested.resolve()


def test_resolve_existing_path_handles_relative_backslash_paths_against_base_dir(tmp_path):
    nested = tmp_path / "data" / "mineru_cache" / "chapter" / "figure.png"
    nested.parent.mkdir(parents=True)
    nested.write_bytes(b"image")

    resolved = resolve_existing_path(r"data\mineru_cache\chapter\figure.png", base_dir=tmp_path, runtime="linux")

    assert resolved == nested.resolve()


def test_resolve_project_path_anchors_relative_path_to_project_root(monkeypatch, tmp_path):
    monkeypatch.setattr(platform_paths, "_PROJECT_ROOT", tmp_path)

    resolved = resolve_project_path("data/mineru_cache/chapter/full.md")

    assert resolved == (tmp_path / "data" / "mineru_cache" / "chapter" / "full.md").resolve()


def test_resolve_existing_path_uses_project_root_for_relative_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(platform_paths, "_PROJECT_ROOT", tmp_path)
    nested = tmp_path / "frontend" / "index.html"
    nested.parent.mkdir(parents=True)
    nested.write_text("ok", encoding="utf-8")

    resolved = resolve_existing_path("frontend/index.html")

    assert resolved == nested.resolve()


def test_project_relative_path_returns_repo_relative_posix(monkeypatch, tmp_path):
    monkeypatch.setattr(platform_paths, "_PROJECT_ROOT", tmp_path)
    target = tmp_path / "data" / "media_evidence_index" / "batch_summary.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}", encoding="utf-8")

    assert project_relative_path(target) == "data/media_evidence_index/batch_summary.json"


def test_project_relative_path_keeps_relative_paths_independent_of_cwd(monkeypatch, tmp_path):
    project = tmp_path / "repo"
    cwd = project / "scripts"
    cwd.mkdir(parents=True)
    monkeypatch.setattr(platform_paths, "_PROJECT_ROOT", project)
    monkeypatch.chdir(cwd)

    assert project_relative_path("runtime/cache/chapter/full.md") == "runtime/cache/chapter/full.md"
    assert project_relative_path(r"runtime\cache\chapter\figure.png") == "runtime/cache/chapter/figure.png"


def test_runtime_platform_returns_supported_label():
    assert runtime_platform() in {"windows", "wsl", "linux", "macos"}

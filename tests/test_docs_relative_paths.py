from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Scan all tracked .md files in docs/, plus root README and CONTRIBUTING
DOCS_TO_CHECK = sorted(
    path
    for path in PROJECT_ROOT.rglob("*.md")
    if ".git/" not in str(path)
    and "node_modules/" not in str(path)
    and ".pytest_cache/" not in str(path)
    and "kg_builder_standalone/outputs/" not in str(path)
)


FORBIDDEN_SNIPPETS = [
    "/home/haizi/ai-tutor-agent",
    "cd /home/haizi/ai-tutor-agent",
]


def test_all_docs_do_not_embed_machine_specific_repo_paths():
    failures = []
    for doc in DOCS_TO_CHECK:
        rel = doc.relative_to(PROJECT_ROOT)
        content = doc.read_text(encoding="utf-8")
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in content:
                failures.append(f"{rel} contains: {snippet}")
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize("doc_path", DOCS_TO_CHECK, ids=lambda p: str(p.relative_to(PROJECT_ROOT)))
def test_each_doc_no_machine_path(doc_path):
    """Parametrize for clearer failure location per file."""
    rel = doc_path.relative_to(PROJECT_ROOT)
    content = doc_path.read_text(encoding="utf-8")
    for snippet in FORBIDDEN_SNIPPETS:
        assert snippet not in content, f"{rel} contains machine-specific path: {snippet}"

from pathlib import Path


DOCS_TO_CHECK = [
    Path("README.md"),
    Path("docs/current-status-and-usage.md"),
    Path("docs/next-iteration-plan.md"),
    Path("docs/reports/2026-04-28-langgraph-final-closure-report.md"),
    Path("docs/reports/2026-04-28-langgraph-mainflow-completion-report.md"),
]


FORBIDDEN_SNIPPETS = [
    "/home/haizi/ai-tutor-agent",
    "cd /home/haizi/ai-tutor-agent",
]


def test_docs_do_not_embed_machine_specific_repo_paths():
    for doc in DOCS_TO_CHECK:
        content = doc.read_text(encoding="utf-8")
        for snippet in FORBIDDEN_SNIPPETS:
            assert snippet not in content, f"{doc} still contains machine-specific path: {snippet}"

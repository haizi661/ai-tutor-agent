# Artificial Intelligence Course Materials

Put the artificial intelligence textbook PDFs here before running the offline build command.

Expected workflow:

```powershell
python -m ai_tutor_agent.ai_learning_path.build_ai_course_assets --node-size 200 --skip-edge-llm
```

If a PDF is too large, fill `chapter_splits.example.json` with 1-based inclusive
page ranges. The offline command will use it when `chapter_splits.json` is not
present, split that PDF into `splits/*.pdf`, and call MinerU on the split files.

To only validate and split PDFs without calling MinerU:

```powershell
python -m ai_tutor_agent.ai_learning_path.build_ai_course_assets --split-only
```

Notes:

- `python main.py` does not read this directory and does not run MinerU.
- PDF files in this directory are ignored by git.
- `chapter_splits.json` is local runtime input and is ignored by git.
- MinerU outputs are cached under `data/mineru_cache/artificial_intelligence`.
- Generated graph files are written under `data/knowledge_map_outputs/artificial_intelligence`.

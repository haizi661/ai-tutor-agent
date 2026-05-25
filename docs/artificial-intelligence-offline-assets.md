# Artificial Intelligence Offline Asset Build

This project must not run MinerU during `python main.py`.

For the artificial intelligence course, textbook processing is a one-shot offline step:

1. Put AI textbook PDFs in:

```text
data/course_materials/artificial_intelligence/
```

2. Run the offline builder manually:

```powershell
python -m ai_tutor_agent.ai_learning_path.build_ai_course_assets --node-size 200 --skip-edge-llm
```

If a large PDF needs chapter splitting, edit:

```text
data/course_materials/artificial_intelligence/chapter_splits.example.json
```

and fill in 1-based inclusive page ranges:

```json
{
  "documents": [
    {
      "source": "LeeDL_Tutorial_v.1.1.8.pdf",
      "chapters": [
        {
          "chapter_id": "leedl_chapter_01",
          "title": "Introduction",
          "start_page": 1,
          "end_page": 30
        }
      ]
    }
  ]
}
```

The offline command writes split PDFs to `data/course_materials/artificial_intelligence/splits/`
and sends those chapter PDFs to MinerU instead of the original large file.

To split and validate only:

```powershell
python -m ai_tutor_agent.ai_learning_path.build_ai_course_assets --split-only
```

3. Start the app normally:

```powershell
python main.py
```

Runtime reads produced assets only:

- `data/knowledge_map_outputs/artificial_intelligence/ai_nodes.csv`
- `data/knowledge_map_outputs/artificial_intelligence/ai_edges.csv`
- `data/mineru_cache/artificial_intelligence/**`
- `data/media_evidence_index/artificial_intelligence/**`

Useful modes:

```powershell
python -m ai_tutor_agent.ai_learning_path.build_ai_course_assets --dry-run
python -m ai_tutor_agent.ai_learning_path.build_ai_course_assets --split-only
python -m ai_tutor_agent.ai_learning_path.build_ai_course_assets --mineru-only
python -m ai_tutor_agent.ai_learning_path.build_ai_course_assets --skip-mineru --skip-node-generation --skip-edge-generation
```

The current AI nodes/edges generator still uses `data/ai_knowledge_seed/*.txt` plus DeepSeek prompts. MinerU output is prepared as course evidence for later media indexing and GraphRAG use; it is intentionally not triggered from the web runtime.

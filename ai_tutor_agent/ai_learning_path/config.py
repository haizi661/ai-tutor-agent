from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

AI_SEED_DIR = PROJECT_ROOT / "data" / "ai_knowledge_seed"
AI_CONCEPTS_20 = AI_SEED_DIR / "ai_concepts.txt"
AI_CONCEPTS_200 = AI_SEED_DIR / "ai_concepts200.txt"

AI_OUTPUT_DIR = PROJECT_ROOT / "data" / "knowledge_map_outputs" / "artificial_intelligence"
AI_NODES_CSV = AI_OUTPUT_DIR / "ai_nodes.csv"
AI_EDGES_CSV = AI_OUTPUT_DIR / "ai_edges.csv"

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
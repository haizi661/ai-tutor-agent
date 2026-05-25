from pathlib import Path

from ai_tutor_agent.course_assets import get_course_assets

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AI_COURSE_ASSETS = get_course_assets("artificial_intelligence")

AI_STUDENT_STATE_JSON = AI_COURSE_ASSETS.resolve("student_state_path")
AI_STUDENT_STATE_DIR = AI_STUDENT_STATE_JSON.parent

AI_SEED_DIR = PROJECT_ROOT / "data" / "ai_knowledge_seed"
AI_CONCEPTS_20 = AI_SEED_DIR / "ai_concepts.txt"
AI_CONCEPTS_200 = AI_SEED_DIR / "ai_concepts200.txt"
AI_NODE_CHAPTER_MAP = AI_SEED_DIR / "ai_node_chapter_map.json"

AI_NODES_CSV = AI_COURSE_ASSETS.resolve("nodes_csv_path")
AI_EDGES_CSV = AI_COURSE_ASSETS.resolve("edges_csv_path")
AI_OUTPUT_DIR = AI_NODES_CSV.parent

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

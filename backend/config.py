import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
IMAGES_DIR = BASE_DIR / "images"

UPLOAD_DIR.mkdir(exist_ok=True)

# --- DashScope / Qwen (阿里百炼) ---
DASHSCOPE_API_KEY = os.getenv("QW_AUTH_TOKEN", "")
DASHSCOPE_BASE_URL = os.getenv("QW_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
VISION_MODEL = os.getenv("QW_MODEL", "qwen-vl-max")
VISION_MODEL_FALLBACK = os.getenv("VISION_MODEL_FALLBACK", "qwen-vl-plus")

# --- DeepSeek ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_AUTH_TOKEN", "")
# Use the standard OpenAI-compatible base (env var points to /anthropic endpoint)
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
REASONING_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-reasoner")
THINKING_BUDGET = 4096
MAX_TOKENS = 8192

# --- Server ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEMO_MODE = os.getenv("DEMO_MODE", "").lower() == "true"

# --- CLIP ---
CLIP_MODEL_NAME = "OFA-Sys/chinese-clip-vit-large-patch14"
CLIP_CACHE_DIR = os.getenv("CLIP_CACHE_DIR", str(BASE_DIR / "model_cache"))

# --- Cases ---
CASES_FILE = DATA_DIR / "cases.json"
FEATURES_FILE = DATA_DIR / "case_features.npy"
TOP_K_CASES = 5

# --- Limits ---
MAX_IMAGES_NATURAL = 6
MAX_IMAGES_LAMP = 4
MAX_IMAGES_MACRO = 2
MAX_FILE_SIZE_MB = 20

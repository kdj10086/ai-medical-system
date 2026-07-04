import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'medical.db')}"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# JWT
SECRET_KEY = os.environ.get("SECRET_KEY", "ai-medical-secret-key-change-in-production")
JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours

# LLM API (OpenAI-compatible)
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")  # Set to enable real LLM
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

# OCR
OCR_PROVIDER = os.environ.get("OCR_PROVIDER", "mock")  # mock | paddleocr | baidu

# Upload
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Mock mode (auto-detected)
MOCK_LLM = not LLM_API_KEY

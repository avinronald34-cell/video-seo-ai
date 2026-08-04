import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv(
        "FLASK_SECRET_KEY",
        "video-seo-ai-secret-key"
    )

    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "models/gemini-3.6-flash"
)

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # Upload Folder
    UPLOAD_FOLDER = "uploads"

    # Reports
    REPORT_FOLDER = "reports"

    # Max Upload Size
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024

    # Allowed Extensions
    ALLOWED_EXTENSIONS = {
        "mp4",
        "mov",
        "avi",
        "mkv",
        "webm"
    }

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-this-in-render")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "models/gemini-3.6-flash")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

    SCAN_PRICE_RUPEES = 29
    SCAN_PRICE_PAISE = SCAN_PRICE_RUPEES * 100

    UPLOAD_FOLDER = "uploads"
    REPORT_FOLDER = "reports"

    # Keep this conservative on a 512 MB Render instance.
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024

    ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}

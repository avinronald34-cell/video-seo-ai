import os

from dotenv import load_dotenv


# Load local .env values.
# On Render, environment variables are loaded
# directly from the service configuration.
load_dotenv()


class Config:

    # =====================================================
    # FLASK
    # =====================================================

    SECRET_KEY = os.getenv(
        "FLASK_SECRET_KEY",
        "change-this-in-render"
    )

    # =====================================================
    # GEMINI
    # =====================================================

    GEMINI_API_KEY = os.getenv(
        "GEMINI_API_KEY"
    )

    MODEL_NAME = os.getenv(
        "MODEL_NAME",
        "models/gemini-3.6-flash"
    )

    # =====================================================
    # GOOGLE OAUTH
    # =====================================================

    GOOGLE_CLIENT_ID = os.getenv(
        "GOOGLE_CLIENT_ID"
    )

    GOOGLE_CLIENT_SECRET = os.getenv(
        "GOOGLE_CLIENT_SECRET"
    )

    # =====================================================
    # RAZORPAY
    # =====================================================

    RAZORPAY_KEY_ID = os.getenv(
        "RAZORPAY_KEY_ID"
    )

    RAZORPAY_KEY_SECRET = os.getenv(
        "RAZORPAY_KEY_SECRET"
    )

    # =====================================================
    # PRICING
    # =====================================================

    SCAN_PRICE_RUPEES = 29

    SCAN_PRICE_PAISE = (
        SCAN_PRICE_RUPEES
        * 100
    )

    # =====================================================
    # FILE STORAGE
    # =====================================================

    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        "uploads"
    )

    REPORT_FOLDER = os.getenv(
        "REPORT_FOLDER",
        "reports"
    )

    # Keep this conservative for the
    # 512 MB Render instance.
    MAX_CONTENT_LENGTH = (
        100
        * 1024
        * 1024
    )

    # =====================================================
    # ALLOWED VIDEO TYPES
    # =====================================================

    ALLOWED_EXTENSIONS = {

        "mp4",

        "mov",

        "avi",

        "mkv",

        "webm"

    }
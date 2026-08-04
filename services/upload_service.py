import os

from werkzeug.utils import secure_filename

from config import Config


class UploadService:

    @staticmethod
    def allowed(filename):

        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower()
            in Config.ALLOWED_EXTENSIONS
        )

    @staticmethod
    def save(file):

        if file.filename == "":
            raise Exception("No file selected.")

        if not UploadService.allowed(file.filename):
            raise Exception(
                "Unsupported file format."
            )

        os.makedirs(
            Config.UPLOAD_FOLDER,
            exist_ok=True
        )

        filename = secure_filename(
            file.filename
        )

        filepath = os.path.join(
            Config.UPLOAD_FOLDER,
            filename
        )

        file.save(filepath)

        return filepath
from pathlib import Path
import tempfile
import zipfile
import shutil


class ZipTools:

    @staticmethod
    def extract_repository(zip_bytes: bytes):

        temp_dir = tempfile.mkdtemp()

        zip_path = Path(temp_dir) / "repository.zip"

        with open(zip_path, "wb") as f:
            f.write(zip_bytes)

        extract_path = Path(temp_dir) / "repository"

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        return temp_dir, extract_path

    @staticmethod
    def cleanup(temp_dir: str):

        shutil.rmtree(temp_dir, ignore_errors=True)
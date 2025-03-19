
from openai import OpenAI
from pathlib import Path


class KimiFileManager:

    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1",
        )

    def create(self, path: Path) -> str:
        file_object = self.client.files.create(file=path, purpose="file-extract")
        return file_object.id

    def get_file(self, file_id: str) -> str:
        return self.client.files.content(file_id=file_id).text





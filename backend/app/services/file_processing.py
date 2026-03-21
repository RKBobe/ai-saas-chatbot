import os

class FileProcessor:
    @staticmethod
    def read_markdown_file(file_path: str) -> str:
        if not os.path.exists(file_path):
            return ''
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def split_into_chunks(text: str, delimiter: str = '\n\n') -> list:
        return [c.strip() for c in text.split(delimiter) if c.strip()]

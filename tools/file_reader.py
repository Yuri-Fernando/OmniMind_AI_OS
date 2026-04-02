# tools/file_reader.py
import os

class FileReaderTool:
    """Ferramenta para ler arquivos locais."""

    def read_text_file(self, file_path):
        if not os.path.exists(file_path):
            return f"Arquivo não encontrado: {file_path}"
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def read_lines(self, file_path, n_lines=10):
        """Lê as primeiras n linhas de um arquivo."""
        if not os.path.exists(file_path):
            return f"Arquivo não encontrado: {file_path}"
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [next(f).strip() for _ in range(n_lines)]
        return "\n".join(lines)
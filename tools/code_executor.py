# tools/code_executor.py
import io
import sys
import traceback

class CodeExecutorTool:
    """Ferramenta para executar código Python dinamicamente."""

    def execute(self, code: str):
        """
        Executa código Python e retorna stdout ou erro.
        """
        try:
            # Redireciona saída
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()

            exec(code, {})
            sys.stdout = old_stdout
            return buffer.getvalue()
        except Exception:
            sys.stdout = old_stdout
            return traceback.format_exc()
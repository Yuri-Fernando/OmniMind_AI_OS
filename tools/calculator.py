"""Ferramenta de calculadora — avalia expressões matemáticas Python com segurança."""
import math


# Contexto seguro: apenas funções matemáticas, sem builtins perigosos
_SAFE_GLOBALS = {
    "__builtins__": {},
    "abs": abs, "round": round, "min": min, "max": max, "sum": sum,
    "pow": pow, "int": int, "float": float,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "pi": math.pi, "e": math.e, "ceil": math.ceil, "floor": math.floor,
}


class CalculatorTool:
    def run(self, expression: str) -> str:
        try:
            result = eval(expression, _SAFE_GLOBALS, {})
            return str(result)
        except ZeroDivisionError:
            return "Erro: divisão por zero"
        except Exception as e:
            return f"Erro ao calcular '{expression}': {e}"

"""Ferramenta de calculadora segura (sem eval)."""
import ast, operator

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv,
}

def _eval(node):
    if isinstance(node, ast.Constant):
        return node.n
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError(f"Operação não suportada: {type(node)}")

def calculate(expression: str) -> dict:
    """Avalia uma expressão matemática de forma segura."""
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval(tree.body)
        return {"expression": expression, "result": result, "ok": True}
    except Exception as e:
        return {"expression": expression, "error": str(e), "ok": False}

# Interface compatível com tool_registry
class CalculatorTool:
    name = "calculator"
    description = "Avalia expressões matemáticas. Input: string com expressão, ex: '2 + 3 * 4'"

    def run(self, expression: str) -> str:
        r = calculate(expression)
        if r["ok"]:
            return f"{expression} = {r['result']}"
        return f"Erro: {r['error']}"

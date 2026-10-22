"""Tool-call accuracy: avalia o COMPORTAMENTO do agente, não só o texto da resposta.

Para cada chamada de ferramenta verifica, de forma determinística (sem LLM):

    tool_match     ferramenta esperada == ferramenta chamada
    args_valid     argumentos obedecem ao esquema (chaves exatas, tipos, não vazios)
    args_match     argumentos == esperados (após normalização)
    result_used    a resposta final usa o valor devolvido pela ferramenta
    grounded       os números/entidades da resposta final são sustentados pelo resultado/contexto

Exemplo (o do plano de melhorias):
    Expected tool: search_document / Actual tool: search_document
    Args valid: yes / Result used: yes / Final answer grounded: yes

`result_used` e `grounded` só são aplicáveis quando há resposta final; sem ela ficam `None`
(não contam nem a favor nem contra — nada de nota inventada).
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Fonte única do esquema de ferramentas (espelha tools/*.py).
DEFAULT_TOOL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "calculator": {"required": {"expression": "string"}},
    "weather_api": {"required": {"city": "string"}},
    "web_search": {"required": {"query": "string"}},
    "file_reader": {"required": {"path": "string"}},
    "none": {"required": {}},
}
_TYPES = {"string": str, "number": (int, float), "boolean": bool, "object": dict, "array": list}


# ------------------------------------------------------------------ parsing
def extract_json_object(text: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    """Devolve (objeto, estrito). `estrito` = a saída INTEIRA é o JSON (sem texto extra/cerca de código)."""
    text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj, True
    except Exception:
        pass
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I).strip()
    start = cleaned.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(cleaned)):
            depth += cleaned[i] == "{"
            depth -= cleaned[i] == "}"
            if depth == 0:
                try:
                    obj = json.loads(cleaned[start:i + 1])
                    if isinstance(obj, dict):
                        return obj, False
                except Exception:
                    break
                break
        start = cleaned.find("{", start + 1)
    return None, False


def _norm_text(v: Any) -> str:
    s = unicodedata.normalize("NFKC", str(v)).strip().casefold()
    return re.sub(r"\s+", " ", s)


def normalize_args(tool: str, args: Dict[str, Any]) -> Dict[str, str]:
    out = {}
    for k, v in (args or {}).items():
        s = _norm_text(v)
        if tool == "calculator" and k == "expression":
            s = re.sub(r"\s+", "", s)
        out[str(k)] = s
    return out


def validate_args(tool: str, args: Any, schemas: Dict[str, Dict[str, Any]] = DEFAULT_TOOL_SCHEMAS) -> List[str]:
    if tool not in schemas:
        return [f"ferramenta desconhecida: {tool!r}"]
    if not isinstance(args, dict):
        return ["args não é um objeto"]
    required = schemas[tool]["required"]
    errs = []
    for k in required:
        if k not in args:
            errs.append(f"falta o argumento {k!r}")
    for k, v in args.items():
        if k not in required:
            errs.append(f"argumento inesperado {k!r}")
            continue
        typ = _TYPES[required[k]]
        if isinstance(v, bool) and required[k] != "boolean" or not isinstance(v, typ):
            errs.append(f"argumento {k!r} com tipo errado")
        elif required[k] == "string" and not v.strip():
            errs.append(f"argumento {k!r} vazio")
    return errs


# ------------------------------------------------------------------ grounding
def _tokens(text: str) -> List[str]:
    return re.findall(r"\w+(?:[.,]\w+)*", _norm_text(text))


def _result_values(result: Any) -> List[str]:
    return _tokens(result if isinstance(result, str) else json.dumps(result, ensure_ascii=False))


def result_used(final_answer: str, result: Any) -> bool:
    """A resposta contém o(s) valor(es) principal(is) do resultado (números e termos longos)."""
    key = [t for t in _result_values(result) if re.search(r"\d", t) or len(t) >= 5]
    if not key:
        return False
    ans = set(_tokens(final_answer))
    return sum(t in ans for t in key) / len(key) >= 0.5


def grounded(final_answer: str, result: Any = None, context: str = "") -> bool:
    """Todo NÚMERO afirmado na resposta aparece no resultado da ferramenta ou no contexto/pergunta."""
    support = set(_result_values(result)) | set(_tokens(context)) if result is not None else set(_tokens(context))
    nums = [t for t in _tokens(final_answer) if re.fullmatch(r"\d+(?:[.,]\d+)?", t)]
    return all(n in support for n in nums)


# ------------------------------------------------------------------ pontuação
@dataclass
class ToolCallScore:
    tool_match: bool
    args_valid: bool
    args_match: bool
    json_valid: bool = True
    json_strict: bool = True
    result_used: Optional[bool] = None
    grounded: Optional[bool] = None
    errors: List[str] = field(default_factory=list)

    @property
    def correct_call(self) -> bool:
        return self.json_valid and self.tool_match and self.args_valid and self.args_match

    @property
    def overall(self) -> bool:
        """Chamada correta E (quando há resposta final) resultado usado e resposta ancorada."""
        extra = [x for x in (self.result_used, self.grounded) if x is not None]
        return self.correct_call and all(extra)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.update(correct_call=self.correct_call, overall=self.overall)
        return d


def score_tool_call(
    expected: Dict[str, Any],
    actual: Optional[Dict[str, Any]],
    schemas: Dict[str, Dict[str, Any]] = DEFAULT_TOOL_SCHEMAS,
    tool_result: Any = None,
    final_answer: Optional[str] = None,
    context: str = "",
    strict_json: bool = True,
) -> ToolCallScore:
    if not isinstance(actual, dict) or "tool" not in actual:
        return ToolCallScore(False, False, False, json_valid=False, json_strict=False,
                             errors=["chamada ausente ou sem campo 'tool'"])
    tool, args = actual.get("tool"), actual.get("args", {})
    errs = validate_args(str(tool), args, schemas)
    tool_match = tool == expected.get("tool")
    args_match = tool_match and not errs and normalize_args(tool, args) == normalize_args(tool, expected.get("args", {}))
    if not tool_match:
        errs.append(f"ferramenta {tool!r} != esperada {expected.get('tool')!r}")
    elif not errs and not args_match:
        errs.append("argumentos diferentes do esperado")
    sc = ToolCallScore(tool_match, not validate_args(str(tool), args, schemas), args_match, True, strict_json, errors=errs)
    if final_answer is not None:
        if expected.get("tool") != "none":              # sem ferramenta não há resultado para usar
            sc.result_used = result_used(final_answer, tool_result) if tool_result is not None else False
        sc.grounded = grounded(final_answer, tool_result, context)
    return sc


def aggregate(scores: Iterable[ToolCallScore]) -> Dict[str, Any]:
    scores = list(scores)
    n = len(scores)
    if not n:
        return {"n": 0}

    def rate(vals):
        vals = [v for v in vals if v is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    return {
        "n": n,
        "json_valid": rate(s.json_valid for s in scores),
        "json_strict": rate(s.json_strict for s in scores),
        "tool_match": rate(s.tool_match for s in scores),
        "args_valid": rate(s.args_valid for s in scores),
        "args_match": rate(s.args_match for s in scores),
        "correct_call": rate(s.correct_call for s in scores),
        "result_used": rate(s.result_used for s in scores),
        "grounded": rate(s.grounded for s in scores),
        "overall": rate(s.overall for s in scores),
    }

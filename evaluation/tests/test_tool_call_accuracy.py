"""Tool-call accuracy: casos positivos e negativos (a métrica tem que FALHAR quando o agente erra)."""
import pytest

from evaluation.tool_call_accuracy import (aggregate, extract_json_object, grounded, normalize_args, result_used,
                                           score_tool_call, validate_args)

CALC = {"tool": "calculator", "args": {"expression": "37*12"}}


# ----------------------------------------------------------------- parsing
def test_extract_strict_json():
    obj, strict = extract_json_object('{"tool":"none","args":{}}')
    assert obj == {"tool": "none", "args": {}} and strict


def test_extract_lenient_json_with_fence_and_noise():
    obj, strict = extract_json_object('Claro!\n```json\n{"tool":"web_search","args":{"query":"a {b}"}}\n```')
    assert obj["tool"] == "web_search" and not strict


@pytest.mark.parametrize("text", ["", "sem json aqui", "{quebrado", '["lista"]'])
def test_extract_returns_none_for_garbage(text):
    assert extract_json_object(text)[0] is None


# ----------------------------------------------------------------- argumentos
def test_validate_args_cases():
    assert validate_args("calculator", {"expression": "1+1"}) == []
    assert validate_args("none", {}) == []
    assert validate_args("calculator", {"expr": "1+1"})                  # chave errada
    assert validate_args("calculator", {"expression": ""})              # vazio
    assert validate_args("calculator", {"expression": 5})               # tipo errado
    assert validate_args("calculator", {"expression": "1", "x": "y"})   # chave extra
    assert validate_args("inexistente", {})                             # ferramenta desconhecida
    assert validate_args("calculator", "texto")                         # args não é objeto


def test_normalization_ignores_case_accents_form_and_calc_spaces():
    assert normalize_args("calculator", {"expression": "37 * 12"}) == normalize_args("calculator", {"expression": "37*12"})
    assert normalize_args("weather_api", {"city": " RECIFE "}) == normalize_args("weather_api", {"city": "recife"})


# ----------------------------------------------------------------- score
def test_perfect_call_and_answer():
    sc = score_tool_call(CALC, CALC, tool_result="444", final_answer="37 vezes 12 é 444.",
                         context="Quanto é 37 vezes 12?")
    assert sc.tool_match and sc.args_valid and sc.args_match and sc.result_used and sc.grounded and sc.overall


def test_wrong_tool_fails():
    sc = score_tool_call(CALC, {"tool": "web_search", "args": {"query": "x"}})
    assert not sc.tool_match and not sc.correct_call and not sc.overall


def test_invalid_args_fail_even_with_right_tool():
    sc = score_tool_call(CALC, {"tool": "calculator", "args": {"expr": "37*12"}})
    assert sc.tool_match and not sc.args_valid and not sc.correct_call


def test_valid_but_wrong_args_fail():
    sc = score_tool_call(CALC, {"tool": "calculator", "args": {"expression": "37*21"}})
    assert sc.args_valid and not sc.args_match and not sc.correct_call


def test_missing_call_fails_cleanly():
    sc = score_tool_call(CALC, None)
    assert not sc.json_valid and not sc.correct_call and sc.errors


def test_result_ignored_is_detected():
    sc = score_tool_call(CALC, CALC, tool_result="444", final_answer="Não sei responder.")
    assert sc.correct_call and sc.result_used is False and not sc.overall


def test_ungrounded_number_is_detected():
    weather = {"tool": "weather_api", "args": {"city": "Curitiba"}}
    sc = score_tool_call(weather, weather, tool_result="Curitiba: nublado +14°C",
                         final_answer="Em Curitiba faz 31 graus.", context="Como está o tempo em Curitiba?")
    assert sc.grounded is False and not sc.overall


def test_no_final_answer_leaves_answer_checks_undefined():
    sc = score_tool_call(CALC, CALC)
    assert sc.result_used is None and sc.grounded is None and sc.overall      # não contam contra


def test_none_tool_has_no_result_to_use():
    none = {"tool": "none", "args": {}}
    sc = score_tool_call(none, none, final_answer="Olá! Tudo bem.", tool_result="")
    assert sc.result_used is None and sc.overall


def test_result_used_and_grounded_helpers():
    assert result_used("São 444 no total", "444") and not result_used("nada", "444")
    assert grounded("Há 14 graus", "+14°C") and not grounded("Há 15 graus", "+14°C")


def test_aggregate_rates_ignore_undefined():
    good = score_tool_call(CALC, CALC, tool_result="444", final_answer="é 444")
    bad = score_tool_call(CALC, {"tool": "web_search", "args": {"query": "x"}})
    agg = aggregate([good, bad])
    assert agg["n"] == 2 and agg["correct_call"] == 0.5 and agg["result_used"] == 1.0   # bad não tem resposta
    assert aggregate([]) == {"n": 0}

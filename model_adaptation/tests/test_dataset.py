"""Dataset sintético: determinismo, esquema, anti-leakage (inclusive que o detector de vazamento DETECTA)."""
import copy
import json

import pytest

from model_adaptation.common import TOOL_SCHEMAS, canonical_target
from model_adaptation.datasets.prepare_dataset import SPLIT_SIZES, build
from model_adaptation.datasets.validation import validate_dataset, validate_record


@pytest.fixture(scope="module")
def splits():
    return build(0)


def test_sizes_match_spec(splits):
    for name, counts in SPLIT_SIZES.items():
        assert len(splits[name]) == sum(counts.values())


def test_validation_passes_with_zero_leakage(splits):
    rep = validate_dataset(splits)
    assert rep["ok"], rep
    assert rep["leakage"] == {"prompt_exato": 0, "prompt_normalizado": 0, "tool_args": 0, "none_prompt": 0}
    assert rep["holdout_template"]["em_train_val"] == 0
    assert rep["holdout_template"]["em_test"] > 0          # test realmente contém formulação nunca vista


def test_deterministic_for_same_seed():
    assert build(3) == build(3)


@pytest.mark.parametrize("seed", [1, 2])
def test_other_seeds_also_leak_free(seed):
    assert validate_dataset(build(seed))["ok"]


def test_every_target_is_canonical_json_matching_schema(splits):
    for rows in splits.values():
        for r in rows:
            assert r["tool"] in TOOL_SCHEMAS
            assert json.loads(r["target"]) == {"tool": r["tool"], "args": r["args"]}
            assert r["target"] == canonical_target(r["tool"], r["args"])
            assert validate_record(r) == []


def test_detector_catches_exact_prompt_leak(splits):
    leaked = copy.deepcopy(splits)
    leaked["test"][0] = dict(leaked["test"][0], prompt=leaked["train"][0]["prompt"])
    rep = validate_dataset(leaked)
    assert not rep["ok"] and rep["leakage"]["prompt_exato"] >= 1


def test_detector_catches_entity_leak_with_different_phrasing(splits):
    leaked = copy.deepcopy(splits)
    victim = next(r for r in leaked["train"] if r["tool"] == "weather_api")
    t = next(r for r in leaked["test"] if r["tool"] == "weather_api")
    t.update(args=dict(victim["args"]), target=canonical_target("weather_api", victim["args"]),
             prompt="frase completamente diferente " + victim["args"]["city"])
    rep = validate_dataset(leaked)
    assert not rep["ok"] and rep["leakage"]["tool_args"] >= 1


def test_detector_catches_holdout_template_in_train(splits):
    bad = copy.deepcopy(splits)
    r = next(x for x in bad["train"] if x["tool"] == "calculator")
    r["template_id"] = 4
    assert not validate_dataset(bad)["ok"]


def test_detector_catches_noncanonical_target(splits):
    bad = copy.deepcopy(splits)
    bad["val"][0]["target"] = '{"tool": "none"}'
    assert not validate_dataset(bad)["ok"]


def test_class_distribution_has_all_tools_in_every_split(splits):
    for rows in splits.values():
        assert {r["tool"] for r in rows} == set(TOOL_SCHEMAS)

import pytest

from vard_eeg_erp.scoring import DOMAINS, score


def configuration():
    return {
        "version": "test-only-1",
        "reference": "synthetic test fixture",
        "normalization": "minmax",
        "domains": {
            code: {
                "definition": "test feature",
                "unit": "uV",
                "minimum": 0,
                "maximum": 10,
                "weight": 1 / 6,
                "direction": "higher",
            }
            for code, _ in DOMAINS
        },
    }


def test_composite_direction_and_clipping():
    model = configuration()
    raw = {code: 2 for code, _ in DOMAINS}
    assert score(model, raw)["composite"] == pytest.approx(20)
    model["domains"]["V1"]["direction"] = "lower"
    assert score(model, raw)["domains"]["V1"]["score"] == 80
    raw["V2"] = 20
    output = score(model, raw)
    assert output["domains"]["V2"]["score"] == 100
    assert output["domains"]["V2"]["outside_reference"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("maximum", 0),
        ("weight", -1),
        ("weight", 0.5),
        ("minimum", float("nan")),
        ("definition", ""),
        ("direction", "unknown"),
    ],
)
def test_invalid_model(key, value):
    model = configuration()
    model["domains"]["V1"][key] = value
    with pytest.raises(ValueError):
        score(model, {code: 2 for code, _ in DOMAINS})


def test_missing_domain_and_nonfinite():
    model = configuration()
    with pytest.raises(ValueError):
        score(model, {"V1": 2})
    with pytest.raises(ValueError):
        score(model, {code: float("inf") for code, _ in DOMAINS})
